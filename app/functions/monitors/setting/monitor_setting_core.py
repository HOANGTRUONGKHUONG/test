from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorSetting as MonitorSettingBase


class MonitorSetting(Monitor):
    def __init__(self):
        log = c_logger("monitor_setting")
        super().__init__(log.log_writer, MonitorSettingBase)

    def get_base_item(self, item):
        if item.status == 1:
            result = "Success"
        else:
            result = "Faild"
      
        base_item = {
            # "id": item.id,
            "ip_address": item.ip_address,
            "datetime": datetime_to_str(item.datetime),
            "user_name": item.user_name,
            "action": item.action,
            "description": item.description,
            "result": result
        }
        return base_item
        
