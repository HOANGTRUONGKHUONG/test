import datetime
import re
import time

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.configuration.firewall import add_ip_to_ips_chain
from app.libraries.location.location_finder import find_country
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available
from app.libraries.system.shell import run_command
from app.libraries.system.sys_time import get_current_time
from app.model.ClickhouseModel import MonitorDdosApplication
from app.setting import MONITOR_LOG_DIR

# ERROR_LOG_FILE_DIR = "/usr/local/openresty/nginx/logs/error.log"
# ACCESS_LOG_FILE_DIR = "/usr/local/openresty/nginx/logs/access.log"
ERROR_LOG_FILE_DIR = "/var/log/nginx/error.log"
ACCESS_LOG_FILE_DIR = "/var/log/nginx/access.log"


def block_ip(ip):
    cdb = ClickhouseBase()
    ips_data = MonitorDdosApplication.objects_in(cdb).filter(MonitorDdosApplication.unlock.__eq__(0),
                                                             MonitorDdosApplication.ip_address.__eq__(ip))
    if ips_data.count() == 0:
        return add_ip_to_ips_chain(ip)
    else:
        print(f"IP: {ip} already block in db")
        logger.error(f"IP: {ip} already block in db")
        # already have a block in db -> already in iptables -> return False
        return False


def extract_log_information(log_lines):
    list_attacker_obj = {}
    for line in log_lines:
        regex = re.compile(r"(?P<datetime>.*?) \[error\].*?limiting requests.*?by zone.*\"(?P<rule>.*?)\".*?"
                           r"client: (?P<attacker_ip>.*?), server: (?P<domain>.*?),.*")
        ddos_event = regex.search(line)
        if ddos_event is not None:
            # print("DDoS event detected")
            event_info = ddos_event.groupdict()
            if event_info['attacker_ip'] not in list_attacker_obj:
                attack_obj = {
                    "attacker_ip": event_info['attacker_ip'],
                    "datetime": event_info['datetime'],
                    "rule": event_info['rule'],
                    "website": event_info['domain'],
                    "country": find_country(event_info['attacker_ip'])
                }
                list_attacker_obj[event_info['attacker_ip']] = attack_obj
            else:
                print("IP already in list")
                pass
        else:
            print("Not a attack event")
            pass
    return list_attacker_obj


def save_event_to_db(event_info):
    print(event_info)
    cdb = ClickhouseBase()
    time1 = datetime.datetime.now()
    attack_time = ":".join(event_info['datetime'].split(" ")[1].split(":")[0:2])
    detail = run_command(f"cat {ACCESS_LOG_FILE_DIR} | grep {event_info['attacker_ip']} "
                         f"| grep {attack_time}").decode()
    time2 = datetime.datetime.now()
    delta_time = time2 - time1
    logger.error(f"Time read access_log = {delta_time}")
    monitor_ddos_obj = MonitorDdosApplication(ip_address=event_info["attacker_ip"],
                                              attacker_country=event_info["country"],
                                              rule=event_info["rule"],
                                              website_domain=event_info["website"],
                                              unlock=0,
                                              detail=detail[:60000])
    try:
        cdb.insert([monitor_ddos_obj])
    except Exception as e:
        logger.error(f"{e}")
    print("DONE")


def process_log_file(last_size):
    log_file = open(ERROR_LOG_FILE_DIR, "r", encoding='utf-8', errors='ignore')
    log_file.seek(0, 2)
    current_size = log_file.tell()
    if current_size > last_size:
        logger.debug(f"Detect new log {get_current_time()}")
        print(f"Detect new log {get_current_time()}")
        extend_size = current_size - last_size
        log_file.seek(last_size)
        new_log = log_file.read(extend_size)
        log_lines = new_log.split("\n")
        list_event_obj = extract_log_information(log_lines)
        for ip in list_event_obj:
            if block_ip(ip):
                logger.info(f"Block {ip}")
                print(f"Block {ip}")
                save_event_to_db(list_event_obj[ip])
            else:
                logger.error(f"Block ip {ip} fail")
        last_size = current_size
        log_file.close()
        return last_size
    elif current_size < last_size:
        logger.debug("Log rotate -> Reset log")
        print("Reset log")
        last_size = 0
        log_file.close()
        return last_size
    else:
        # current size = last size
        logger.debug("No new log entry")
        print("No new log entry")
        log_file.close()
        return current_size


def main():
    print("Monitor DDoS")
    file = open(ERROR_LOG_FILE_DIR, "r")
    file.seek(0, 2)
    last_size = file.tell()
    file.close()
    while True:
        print(last_size)
        last_size = process_log_file(last_size)
        time.sleep(3)


if __name__ == '__main__':
    logger = c_logger(MONITOR_LOG_DIR + "/ddos_service.log").log_writer
    while not check_database_available():
        logger.error("Database not available yet")
        time.sleep(1)
    main()
