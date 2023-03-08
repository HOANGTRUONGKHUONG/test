import time
from datetime import datetime, timedelta

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.configuration.firewall import make_ips_data, delete_ip_in_ips_chain
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available
from app.libraries.system.sys_time import string_to_datetime
from app.model.ClickhouseModel import MonitorDdosApplication
from app.setting import MONITOR_LOG_DIR


def check_rule():
    while True:
        cdb = ClickhouseBase()
        ips_data = make_ips_data()
        for data in ips_data:
            for detail in data["attack_detail"]:
                try:
                    if datetime.now() - string_to_datetime(detail["time_attack"]) >= timedelta(
                            seconds=data["block_time"]) \
                            and detail["unblock_status"] == 0:
                        ip_obj = MonitorDdosApplication.objects_in(cdb). \
                            filter(MonitorDdosApplication.ip_address.__eq__(detail["attack_ip"]),
                                   MonitorDdosApplication.unlock.__eq__(0),
                                   MonitorDdosApplication.datetime.__eq__(detail["time_attack"]))
                        if ip_obj:
                            ip_obj.update(unlock=1)
                            if delete_ip_in_ips_chain(detail['attack_ip']):
                                logger.info("Update rule success")
                            else:
                                logger.error("Update rule failed")
                        else:
                            logger.error("no IP")
                except Exception as e:
                    logger.error(f"{e} failed to run this loop")
                    continue
        time.sleep(10)


if __name__ == '__main__':
    logger = c_logger(MONITOR_LOG_DIR + "/ddos_unlock_ip_service.log").log_writer
    while not check_database_available():
        logger.error("Database not available yet")
        time.sleep(1)
    check_rule()
