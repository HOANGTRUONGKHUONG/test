import os
import time

import netifaces
import psutil

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.cloudflare_config import load_balancers_cloudflare_proxy, get_load_balancers_cloudflare
from app.libraries.data_format.change_data import input_intrface
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available
from app.model import NetworkInterfaceBase
from app.model.ClickhouseModel import MonitorTraffic
from app.setting import MONITOR_LOG_DIR

EXCEPT_INTERFACE = ['lo']
application_zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
token = os.getenv("CLOUDFLARE_TOKEN")


def get_list_interface():
    list_interface = []
    for interface in netifaces.interfaces():
        if interface not in EXCEPT_INTERFACE:
            list_interface.append(interface)
    return list_interface


def get_traffic(traffic_dict):
    list_interface = get_list_interface()
    all_interface = psutil.net_io_counters(pernic=True)
    for interface in list_interface:
        if interface in traffic_dict:
            traffic_data = all_interface[interface]
            traffic_dict[interface] = {
                'interface_name': traffic_dict[interface]['interface_name'],
                'interface_id': traffic_dict[interface]['interface_id'],
                'input': float(traffic_data.bytes_recv) - float(traffic_dict[interface]['old_input']),
                'output': float(traffic_data.bytes_sent) - float(traffic_dict[interface]['old_output']),
                'old_input': float(traffic_data.bytes_recv),
                'old_output': float(traffic_data.bytes_sent)
            }
    return traffic_dict


def save_database(traffic_info):
    cdb = ClickhouseBase()
    try:
        for interface in traffic_info:
            cdb.insert([
                MonitorTraffic(input=int(traffic_info[interface]["input"]),
                               output=int(traffic_info[interface]["output"]),
                               interface_name=traffic_info[interface]["interface_name"],
                               interface_id=int(traffic_info[interface]["interface_id"]))])
        return True
    except Exception as e:
        print("error", e)
        logger.error(e)
        return False


def main():
    print("Monitor Traffic")
    init_session, engine_connect = ORMSession_alter()
    list_interface_obj = init_session.query(NetworkInterfaceBase).all()
    list_interface = get_list_interface()
    print(list_interface)
    traffic_data = {}
    init_interface = psutil.net_io_counters(pernic=True)
    for inter in list_interface_obj:
        if inter.name in list_interface:
            traffic_data[inter.name] = {
                "interface_id": 22,
                "interface_name": inter.name,
                "old_input": init_interface[inter.name].bytes_recv,
                "old_output": init_interface[inter.name].bytes_sent
            }
    init_session.close()
    engine_connect.dispose()

    try:
        # doc file data.txt lay ra dk input on vs input off
        entry_conditions_on = input_intrface('input_on')
        entry_conditions_off = input_intrface('input_off')
        # interface to internet (eno1,...)
        gws = netifaces.gateways()
        interface = gws['default'][netifaces.AF_INET][1]
    except Exception as e:
        raise e
    # call dk ban dau.
    count = 0
    status = get_load_balancers_cloudflare(token, application_zone_id)

    while True:
        count += 1
        traffic_data = get_traffic(traffic_data)
        for interfaces in traffic_data:
            if interface == interfaces:
                # dk turn 'on'
                if status == False and traffic_data[interfaces]["input"] >= entry_conditions_on:
                    # Turn on load balancers cloudflare
                    load_balancers_cloudflare_proxy(token, application_zone_id, "on")
                    # reload dk time and status hien tai.
                    count = 0
                    status = get_load_balancers_cloudflare(token, application_zone_id)
                # dk turn 'off' vs time off 300s.
                if status == True and traffic_data[interfaces]["input"] < entry_conditions_off and count >= 300:
                    # Turn off load balancers cloudflare.
                    load_balancers_cloudflare_proxy(token, application_zone_id, "off")
                    # update status hien tai.
                    status = get_load_balancers_cloudflare(token, application_zone_id)
        # print(status, traffic_data)
        save_database(traffic_data)
        time.sleep(1)


if __name__ == '__main__':
    logger = c_logger(MONITOR_LOG_DIR + '/monitor-traffic-service.log').log_writer
    while not check_database_available():
        logger.error("Database not available yet")
        time.sleep(1)
    main()
