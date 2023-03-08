import re
import threading
import time

from django.template import engines

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.string_format import json_to_string
from app.libraries.location.location_finder import find_country
from app.libraries.logger import c_logger
from app.libraries.system.shell import run_command
from app.libraries.system.sys_time import get_current_time
from app.model import NetworkInterfaceBase, MonitorBandwidthIPBase
from app.setting import MONITOR_LOG_DIR

PERIOD = 10
INTERVAL = 10
NUM_LINES = 10
session, engine_connect = ORMSession_alter()
logger = c_logger(MONITOR_LOG_DIR + '/monitor-traffic-ip-service.log')


def get_interfaces():
    listen_on = []
    list_interface_obj = session.query(NetworkInterfaceBase). \
        filter(NetworkInterfaceBase.active.__eq__(1) and NetworkInterfaceBase.status.__eq__(1)).all()
    for interface_obj in list_interface_obj:
        itf = {
            'id': interface_obj.id,
            'name': interface_obj.name
        }
        listen_on.append(itf)
    return listen_on


def convert_to_byte(value):
    number = float(re.findall(r'([\d.]+)', value)[0])
    if value.find('GB') != -1:
        number = number * 1073741824
    elif value.find('MB') != -1:
        number = number * 1048576
    elif value.find('KB') != -1:
        number = number * 1024
    return f"{number}B"


def get_events_traffic(interface_name):
    output = run_command(f"iftop -s {INTERVAL} -L {NUM_LINES} -i {interface_name} -tnNbB "
                         f"-f 'not ether host ff:ff:ff:ff:ff:ff'")
    if output != "":
        try:
            regex = re.compile(r"[\d.]+\s+=>\s+[\d.]+\w+\s+"
                               r"(?P<input>[\d.]+\w+)\s+[\d.]+\w+\s+[\d.]+\w+\s+"
                               r"(?P<ip_address>[\d.]+)\s+<=\s+[\d.]+\w+\s+"
                               r"(?P<output>[\d.]+\w+)\s+[\d.]+\w+\s+[\d.]+")
            list_traffic = [m.groupdict() for m in regex.finditer(output)]
            for traffic in list_traffic:
                traffic['ip_country'] = find_country(traffic['ip_address'])
                traffic['input'] = convert_to_byte(traffic['input'])
                traffic['output'] = convert_to_byte(traffic['output'])
            return list_traffic
        except Exception as e:
            logger.log_writer.error(e)
            raise e
    else:
        return []


def send_to_db(events, interface_id):
    traffic_ip_obj = MonitorBandwidthIPBase(datetime=get_current_time(),
                                            interface_id=interface_id,
                                            value=json_to_string(events))
    session.add(traffic_ip_obj)
    try:
        session.commit()
    except Exception as e:
        logger.log_writer.error(e)
        raise e
    finally:
        session.close()
        engine_connect.dispose()

def thread_monitor_bandwidth(interface_detail):
    events = get_events_traffic(interface_detail["name"])
    if len(events) != 0:
        send_to_db(events, interface_detail["id"])


while True:
    list_interface = get_interfaces()
    if len(list_interface) != 0:
        threads = []
        for interface in list_interface:
            th = threading.Thread(target=thread_monitor_bandwidth, args=(interface,))
            threads.append(th)
        for thread in threads:
            thread.start()
    else:
        logger.log_writer.debug("Not interface active or Link status off")
    time.sleep(PERIOD)
