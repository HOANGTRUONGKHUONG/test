import time

from django.template import engines

from app.functions.monitors.traffic.monitor_traffic_service import get_list_interface
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available, is_interface_operstate_up
from app.model import NetworkInterfaceBase
from app.setting import MONITOR_LOG_DIR


def save_status_to_db(interface_name, interface_status):
    session, engine_connect = ORMSession_alter()
    interface_obj = session.query(NetworkInterfaceBase). \
        filter(NetworkInterfaceBase.name.__eq__(interface_name)).first()
    interface_obj.status = interface_status
    session.flush()
    try:
        session.commit()
    except Exception as e:
        logger.error(e)
    finally:
        session.close()
        engine_connect.dispose()


def main():
    print("Monitor Interface Status")
    sys_interface = get_list_interface()
    interface_status_obj = {}
    init_session, engine_connect = ORMSession_alter()
    interface_db = init_session.query(NetworkInterfaceBase).all()
    init_session.close()
    engine_connect.dispose()
    for interface in interface_db:
        interface_status_obj[interface.name] = True if interface.status == 1 else False
    while True:
        for interface in sys_interface:
            if interface in interface_status_obj:
                status = is_interface_operstate_up(interface)
                if interface_status_obj[interface] != status:
                    # save db
                    save_status_to_db(interface, status)
                    # update list
                    interface_status_obj[interface] = status
            else:
                logger.debug(f"Interface {interface} not in db")
        print(interface_status_obj)
        time.sleep(10)


if __name__ == '__main__':
    logger = c_logger(MONITOR_LOG_DIR + '/monitor-interface-status-service.log').log_writer
    while not check_database_available():
        logger.error("Database not available yet")
        time.sleep(1)
    main()
