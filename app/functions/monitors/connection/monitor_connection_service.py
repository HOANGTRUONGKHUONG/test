import time

import requests

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available
from app.libraries.system.sys_time import get_current_time
from app.model.ClickhouseModel import MonitorConnection
from app.setting import MONITOR_LOG_DIR

STUB_URL = 'http://localhost:8009/stub_status'


def get_stub_data():
    try:
        r = requests.get(STUB_URL)
        raw = r.text.split(" ")
        response = {
            'active': int(raw[2]),
            'requests': int(raw[9]),
            'reading': int(raw[11]),
            'writing': int(raw[13]),
            'waiting': int(raw[15]),
            'accepts': int(raw[7]),
            'handled': int(raw[8])
        }
        return response
    except Exception as e:
        logger.log_writer.error(e)
    except ConnectionError as e:
        print("Connection error")
        logger.log_writer.error(e)
    return {
        'active': 0,
        'requests': 0,
        'reading': 0,
        'writing': 0,
        'waiting': 0,
        'accepts': 0,
        'handled': 0
    }


def save_to_database(connection_data):
    print(get_current_time(), connection_data)
    cdb = ClickhouseBase()
    connection_obj = MonitorConnection(active=connection_data["active"],
                                       reading=connection_data["reading"],
                                       writing=connection_data["writing"],
                                       waiting=connection_data["waiting"]
                                       )
    try:
        cdb.insert([connection_obj])
    except Exception as e:
        logger.log_writer.error(e)


def run():
    print("Start Monitor Connection")
    while True:
        connection_data = get_stub_data()
        save_to_database(connection_data)
        time.sleep(10)


if __name__ == '__main__':
    logger = c_logger(MONITOR_LOG_DIR + '/monitor-connection-service.log')
    while not check_database_available():
        logger.log_writer.error("Database not available yet")
        time.sleep(1)
    run()
