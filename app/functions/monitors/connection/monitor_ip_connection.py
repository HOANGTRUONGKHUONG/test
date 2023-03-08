

from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorIPConnection


class MonitorIP(Monitor):
    def __init__(self):
        log = c_logger("monitor_ip_connection").log_writer
        super().__init__(log, MonitorIPConnection, ["ip_connect", "request_ip", "unlock"])

    def get_base_item(self, item):
        base_item = {
            "datetime": datetime_to_str(item.datetime),
            "ip_connect": item.ip_connect,
            "request_ip": item.request_ip,
            "unlock": item.unlock
        }
        return base_item


