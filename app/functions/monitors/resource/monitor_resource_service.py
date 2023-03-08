import time

import psutil

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available
from app.libraries.system.sys_time import get_current_time
from app.model.ClickhouseModel import MonitorResource
from app.setting import MONITOR_LOG_DIR


def get_resource():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return {"ram": ram, "cpu": cpu, "disk": disk}


def main():
    print("Monitor resource")
    while True:
        cdb = ClickhouseBase()
        value = get_resource()
        date = get_current_time()
        print(date, value)
        resource_obj = MonitorResource(ram=value["ram"], cpu=value["cpu"], disk=value["disk"])
        try:
            cdb.insert([resource_obj])
        except Exception as e:
            log.error(e)
        time.sleep(10)


if __name__ == '__main__':
    log = c_logger(MONITOR_LOG_DIR + '/monitor-resource-service.log').log_writer
    while not check_database_available():
        log.error("Database not available yet")
        time.sleep(1)
    main()
