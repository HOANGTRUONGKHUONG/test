from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorConnection as MonitorConnectionBase


class MonitorConnection(Monitor):
    def __init__(self):
        log = c_logger("monitor_connection").log_writer
        super().__init__(log, MonitorConnectionBase, ["active", "reading", "writing", "waiting"])

    def get_base_item(self, item):
        base_item = {
            "datetime": datetime_to_str(item.datetime),
            "active": item.active,
            "reading": item.reading,
            "writing": item.writing,
            "waiting": item.waiting
        }
        return base_item
