from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorHTTP


class MonitorHTTPStatus(Monitor):
    def __init__(self):
        log = c_logger("monitor_http")
        super().__init__(log.log_writer, MonitorHTTP, ["code_1", "code_2", "code_3", "code_4", "code_5"])

    def get_base_item(self, item):
        base_item = {
            "datetime": datetime_to_str(item.datetime),
            "code_1": int(item.code_1),
            "code_2": int(item.code_2),
            "code_3": int(item.code_3),
            "code_4": int(item.code_4),
            "code_5": int(item.code_5)
        }
        return base_item
