from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorTraffic as MonitorTrafficBase


class MonitorTraffic(Monitor):
    def __init__(self):
        log = c_logger("monitor_traffic")
        super().__init__(log.log_writer, MonitorTrafficBase, ["input", "output"])

    def get_base_item(self, item):
        try:
            base_item = {
                "datetime": datetime_to_str(item.datetime),
                "input": item.input,
                "output": item.output
            }
            return base_item
        except Exception as e:
            print("error", e)
