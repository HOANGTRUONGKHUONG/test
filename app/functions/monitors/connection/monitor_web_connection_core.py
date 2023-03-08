from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorSiteConnection


class MonitorWebsite(Monitor):
    def __init__(self):
        log = c_logger("monitor_web_connection").log_writer
        super().__init__(log, MonitorSiteConnection, ["site_connect", "request_site"])

    def get_base_item(self, item):
        base_item = {
            "datetime": datetime_to_str(item.datetime),
            "site_connect": item.site_connect,
            "request_site": item.request_site
        }
        return base_item
