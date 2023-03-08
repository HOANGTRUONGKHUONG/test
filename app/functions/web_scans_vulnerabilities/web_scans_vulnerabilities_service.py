import base64
import time
from datetime import datetime, timedelta

import requests

from app.functions.web_scans_vulnerabilities.w3af_api_client.connection import Connection
from app.functions.web_scans_vulnerabilities.w3af_api_client.scan import Scan
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.inout.file import read_json_file, write_json_file
from app.libraries.system.shell import run_command
from app.model import ScanHistoryBase
from app.model import ScanResultDetailBase
from app.model import VulnerabilitiesBase
from app.setting import W3AF_PROFILE_PART

DATA_FROM = "/home/bwaf/bwaf/scans_queue.json"
TIME_FORMAT = '%H:%M'
DATE_FORMAT = '%Y-%m-%d'
conn = Connection('http://127.0.0.1:1234/')
urls = "http://127.0.0.1:1234/scans"
session, engine_connect = ORMSession_alter()
times = (datetime.now() + timedelta(minutes=1)).strftime(TIME_FORMAT)


def push_queue():
    try:
        queue = read_json_file(DATA_FROM)
        url = queue[0]["url"]
        vulner = queue[0]["vulnerability"]
        print("System is running on: ", url)
        check = session.query(VulnerabilitiesBase). \
            filter(VulnerabilitiesBase.id.__eq__(vulner)).first()
        if check:
            profile_part = W3AF_PROFILE_PART + check.part
            print(profile_part)
            with open(profile_part) as f:
                scan_profile = f.read()
            target_urls = [url]
            scan = Scan(conn)
            scan.start(scan_profile, target_urls)
        time.sleep(3)
    except Exception as e:
        queue = []
    session.close()
    engine_connect.dispose()


def split_data(scans_data):
    scan_id = scans_data["items"][0]["id"]
    vulnerability = requests.get(f'{urls}/{scan_id}/kb').json()
    leng = len(vulnerability["items"])
    scan_detail = []
    message = ""
    log_text = requests.get(f'{urls}/{scan_id}/log?page=0').json()
    next_url = log_text["next"]
    while log_text["next"] is not None:
        for i in range(len(log_text["entries"])):
            if log_text["entries"][i]["message"] == "Stopping the core...":
                message = log_text["entries"][i - 1]["message"]
        log_text = requests.get(f"{urls}/{scan_id}/log?page={next_url}").json()
        next_url = next_url + 1
    for i in range(len(log_text["entries"])):
        if log_text["entries"][i]["message"] == "Stopping the core...":
            message = log_text["entries"][i - 1]["message"]
    for i in range(leng):
        request = requests.get(f"{urls}/{scan_id}/kb/{i}").json()
        try:
            link_traffic = request["response_ids"][0]
            traffic_request = requests.get(f"{urls}/{scan_id}/traffic/{link_traffic}").json()
        except Exception:
            traffic_request = {
                "request": "None",
                "response": "None"
            }
        scan = {"name": request["name"], "description": request["desc"],
                "long_description": request["long_description"],
                "severity": request["severity"],
                "URL": request["url"],
                "plugin_name": request["plugin_name"],
                "request": base64.b64decode(traffic_request["request"]),
                "response": base64.b64decode(traffic_request["response"])}
        scan_detail.append(scan)
    information = []
    critical = []
    high = []
    medium = []
    low = []
    sorted_scan_detail = []
    for detail in scan_detail:
        if detail['severity'] == 'Information':
            information.append(detail)
        if detail['severity'] == 'Critical':
            critical.append(detail)
        if detail['severity'] == 'High':
            high.append(detail)
        if detail['severity'] == 'Medium':
            medium.append(detail)
        if detail['severity'] == 'Low':
            low.append(detail)
    sorted_scan_detail = critical + high + medium + low + information
    request_server = requests.get(f"{urls}/{scan_id}/kb/0").json()
    try:
        server_name = request_server["attributes"]["server"]
    except Exception:
        server_name = "No Data"
    scan_detail_data = {
        "scan_id": scans_data["items"][0]["id"],
        "website_name": scans_data["items"][0]["target_urls"],
        "system_detail": server_name,
        "date_time": log_text["entries"][0]["time"],
        "status": scans_data["items"][0]["status"],
        "scan finish in": message.split("Scan finished in ")[1],
        "progress": requests.get(f"{urls}/{scan_id}/status").json()[
            "progress"],
        "vulnerability": {
            "total": len(vulnerability["items"]),
            "vulnerability_detail": sorted_scan_detail
        }
    }
    return scan_detail_data


def scan_web_current():
    while True:
        scans = requests.get(urls).json()
        response = scans["items"]
        if not response:
            # chua co du lieu chay. Hang doi rong
            push_queue()
        elif response[0]["status"] == "Running":
            pass
        else:
            time.sleep(10)
            # get du lieu xoa hang cho day db
            try:
                type_scan = read_json_file(DATA_FROM)[0]["type"]
            except Exception as e:
                type_scan = ""
            scanned_data = ScanHistoryBase(
                datetime=datetime.strptime(split_data(scans)["date_time"], "%a %b %d %H:%M:%S %Y"),
                website=split_data(scans)["website_name"][0],
                status=split_data(scans)["status"],
                scan_type=type_scan,
                total_vulner=split_data(scans)["vulnerability"]["total"],
                ip=
                str(run_command(f'ping {split_data(scans)["website_name"][0]} -c1')).split(" ")[2].split(
                    "(")[1].split(")")[0],
                system_detail=split_data(scans)["system_detail"]
            )
            session.add(scanned_data)
            check = datetime.strptime(split_data(scans)["date_time"], "%a %b %d %H:%M:%S %Y")
            select = session.query(ScanHistoryBase).filter(ScanHistoryBase.datetime.__eq__(check)).first()
            for i in split_data(scans)["vulnerability"]["vulnerability_detail"]:
                vulner_description = "SEVERITY: [" + str(i["severity"]) + "], " + "DESCRIPTION: [" + str(
                    i["description"]) + "], " + "REQUEST: [" + str(i["request"]) + "], " + "RESPONSE: [" + str(
                    i["response"]) + "]"
               
                if len(vulner_description) > 50000:
                    scanned_detail = ScanResultDetailBase(vulnerability_name=i["name"],
                                                          history_id=select.id)

                else:
                    scanned_detail = ScanResultDetailBase(vulnerability_name=i["name"],
                                                          description=vulner_description,
                                                          history_id=select.id)

                session.add(scanned_detail)
            session.flush()
            try:
                session.commit()
            except Exception as e:
                print(e)
            cleanup = requests.delete(f"{urls}/{split_data(scans)['scan_id']}")
            queue = read_json_file(DATA_FROM)
            queue.pop(0)
            write_json_file(DATA_FROM, queue)
            session.close()
            engine_connect.dispose()
            print("Done! Waiting for new session")
        time.sleep(5)


if __name__ == '__main__':
    scan_web_current()
