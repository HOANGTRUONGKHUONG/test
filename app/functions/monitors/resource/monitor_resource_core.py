from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorResource


class MonitorResourceCore(Monitor):
    def __init__(self):
        log = c_logger("monitor_resource")
        super().__init__(log.log_writer, MonitorResource, ["cpu", "ram", "disk"])

    def get_base_item(self, item):
        base_item = {
            "datetime": datetime_to_str(item.datetime),
            "cpu": item.cpu,
            "ram": item.ram,
            "disk": item.disk
        }
        return base_item
