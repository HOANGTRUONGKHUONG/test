from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_default_value, filter_datetime, \
    advanced_filter, get_search_value
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.file_export import monitor_export_data
from app.libraries.http.response import *
from app.libraries.inout.file import read_json_file, write_json_file
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import ScanHistoryBase
from app.model import VulnerabilitiesBase, ScanResultDetailBase

DATA_FROM = "/home/bwaf/bwaf/scans_queue.json"


class WebScans(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.len = self.session.query(ScanHistoryBase.id).count()
        self.logger = c_logger("Web_scan").log_writer

    def get_list_log_file(self):
        base_data = [
            {
                "logfile_id": 1,
                "logfile_name": "TestLog1"
            },
            {
                "logfile_id": 2,
                "logfile_name": "TestLog2"
            },
            {
                "logfile_id": 3,
                "logfile_name": "TestLog3"
            },
            {
                "logfile_id": 4,
                "logfile_name": "TestLog4"
            },
            {
                "logfile_id": 5,
                "logfile_name": "TestLog5"
            }
        ]
        return base_data

    def get_vulnerability(self):
        list_vulner_id = self.session.query(VulnerabilitiesBase.id)
        all_vulner_base_data = []
        for vulner in list_vulner_id:
            all_vulner_base_data.append(self.read_vulnerabilities(vulner.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(all_vulner_base_data)

    def create_data_scan(self, scan_json_data):
        try:
            queue = read_json_file(DATA_FROM)
        except Exception as e:
            queue = []
        queue_url = []
        for i in scan_json_data["websites"]:
            scan_data = {
                "url": i,
                "vulnerability": scan_json_data["vulnerability_id"],
                "type": "current"
            }
            queue.append(scan_data)
        write_json_file(DATA_FROM, queue)
        for i in queue:
            queue_url.append(i["url"])
        return status_code_200("post.scan.record.success.System.are.running", queue_url)

    def get_result(self, http_parameters):
        limit, offset, order = get_default_value(self.logger, http_parameters, ScanHistoryBase)
        list_scan = self.session.query(ScanHistoryBase)
        # advance filter result
        # datetime filter
        list_scan = filter_datetime(http_parameters, self.logger, list_scan, ScanHistoryBase)
        # value filter
        list_scan = advanced_filter(http_parameters, self.logger, list_scan, ScanHistoryBase)
        # optional parameter
        list_scan = get_search_value(http_parameters, self.logger, list_scan, ScanHistoryBase)
        # group result
        list_scan = list_scan.group_by(ScanHistoryBase.id).order_by(order)
        list_scan = list_scan.filter(ScanHistoryBase.scan_type.__eq__("current"))
        number_of_value = list_scan.count()
        list_scan = list_scan.limit(limit).offset(offset).all()
        all_scan_data_base = []
        for item in list_scan:
            all_scan_data_base.append(self.read_one_scan(item.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_scan_data_base, number_of_value, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def get_one_scan(self, id):
        scan_inform = self.session.query(ScanResultDetailBase.id). \
            filter(ScanResultDetailBase.history_id.__eq__(id)).all()
        data = []
        Base_data = {}
        for i in scan_inform:
            data.append(self.read_history_detail(i.id))
        Base_data.update(self.read_detail_scan(id))
        return_data = {
            "scan_detail": {
                "total": self.read_one_scan(id)["scan"],
                "detail": data
            }
        }
        Base_data.update(return_data)
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(Base_data)

    def download_scanned_file(self, id):
        download_inform = self.session.query(ScanResultDetailBase.id). \
            filter(ScanResultDetailBase.history_id.__eq__(id)).all()
        data = []
        Base_data = {}
        dowload_data = []
        for i in download_inform:
            data.append(self.read_history_detail(i.id))
        Base_data.update(self.read_detail_scan(id))
        return_data = {
            "scan_detail": {
                "total": self.read_one_scan(id)["scan"],
                "detail": data
            }
        }
        Base_data.update(return_data)
        dowload_data.append(Base_data)
        monitor_setting = log_setting(action="Web Scan", status=1, description="Download web scan record")
        self.session.close()
        self.engine_connect.dispose()
        return monitor_export_data(dowload_data)

    def delete_scan(self, id):
        try:
            self.session.query(ScanHistoryBase).filter(ScanHistoryBase.id.__eq__(id)).delete()
        except Exception as e:
            self.logger.error(e)
            monitor_setting = log_setting(action="Web Scan", status=0, description="Delete web scan record failed")
            return status_code_400("delete.scan.fail.client")
        try:
            self.session.commit()
            monitor_setting = log_setting(action="Web Scan", status=1, description="Delete web scan record")
            return status_code_200("delete.scan.success", {})
        except Exception as e:
            self.logger.error(f"delete scan fail {e} ")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        monitor_setting = log_setting(action="Web Scan", status=0, description="Delete web scan record failed")
        return status_code_500("delete.scan.fail.server")

    def read_vulnerabilities(self, vulnerabilities_id):
        vulner_detail = self.session.query(VulnerabilitiesBase).filter(
            VulnerabilitiesBase.id.__eq__(vulnerabilities_id)).first()
        if vulner_detail:
            vulner_base_data = {
                "vulnerability_id": vulner_detail.id,
                "vulnerability_name": vulner_detail.name,
            }
            return vulner_base_data
        else:
            return {}

    def read_one_scan(self, id):
        one_history = self.session.query(ScanHistoryBase).filter(ScanHistoryBase.id.__eq__(id)).first()
        if one_history:
            history_base_data = {
                "scan_id": one_history.id,
                "website_name": [one_history.website],
                "datetime": str(one_history.datetime),
                "status": int(bool(one_history.status)),
                "scan": one_history.total_vulner,
                "ip": one_history.ip,
                "progress": 100,
                "system_detail": one_history.system_detail
            }
            return history_base_data
        else:
            return {}

    def read_history_detail(self, id):
        history_detail = self.session.query(ScanResultDetailBase).filter(
            ScanResultDetailBase.id.__eq__(id)).first()
        if history_detail:
            history_detail_base_data = {
                "count": 1,
                "name": history_detail.vulnerability_name,
                "description": history_detail.description
            }
            return history_detail_base_data
        return {}

    def read_detail_scan(self, id):
        one_history = self.session.query(ScanHistoryBase).filter(ScanHistoryBase.id.__eq__(id)).first()
        if one_history:
            history_base_data = {
                "scan_id": one_history.id,
                "website_name": [one_history.website],
                "datetime": str(one_history.datetime),
                "status": int(bool(one_history.status)),
                "ip": one_history.ip,
                "progress": 100,
                "system_detail": one_history.system_detail
            }
            return history_base_data
        else:
            return {}
