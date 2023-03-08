import re
import time

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.data_format.ngx_file_conf import ngx_log_format
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available
from app.libraries.system.sys_time import get_current_time
from app.model.ClickhouseModel import MonitorHTTP, MonitorSiteConnection, MonitorIPConnection
from app.setting import MONITOR_LOG_DIR

# Lay ra thong tin {log_format main '....' } trong file nginx.conf.
LOG_FORMAT = ngx_log_format()

# LOG_FORMAT = '$remote_addr - $remote_user [$time_local] "$request" ' \
#              '$status $body_bytes_sent "$http_referer" ' \
#              '"$http_user_agent" "$http_x_forwarded_for"'

#LOG_FILE_DIR = '/var/log/nginx/access.log'
LOG_FILE_DIR = '/usr/local/openresty/nginx/logs/access.log'


# LOG_FILE_DIR = '/home/nhh/Documents/access.log.1'


def log_regex_generator(log_conf):
    patterns = {
        'remote_addr': r'(?:\d{1,3}\.){3}\d{1,3}',
        'upstream_addr': r'.+'
    }
    regex = ''.join(
        '(?P<%s>%s)' % (g, patterns.get(g, '.*?')) if g else re.escape(c)
        for g, c in re.findall(r'\$(\w+)|(.)', log_conf))
    return regex


LOG_REGEX = log_regex_generator(LOG_FORMAT)


def process_log_to_info(log_entry):
    regex = re.compile(LOG_REGEX)
    log_data = [m.groupdict() for m in regex.finditer(log_entry)]
    return log_data


def count_status_code(list_log_obj):
    status_code_obj = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0
    }
    for log_obj in list_log_obj:
        code = str(int(log_obj['status']) // 100)
        status_code_obj[code] += 1
    return status_code_obj


# count site connect
def count_site_connect(list_log_obj):
    request_site = {}
    for line_obj in list_log_obj:
        item_domain = line_obj['server_name']
        if item_domain != '127.0.0.1':
            if item_domain not in request_site:
                request_site[item_domain] = 1
            else:
                request_site[item_domain] += 1
    return request_site


# count ip connect
def count_ip_connect(list_log_obj):
    request_ip = {}
    for line_obj in list_log_obj:
        item_ip = line_obj['remote_addr']
        if item_ip != '127.0.0.1':
            if item_ip not in request_ip:
                request_ip[item_ip] = 1
            else:
                request_ip[item_ip] += 1
    return request_ip


def save_to_database(status_code_obj):
    date = get_current_time()
    print("save_to_database: ", date, status_code_obj)
    cdb = ClickhouseBase()
    # code_2 need to remove 1 request from monitor connection service
    http_obj = MonitorHTTP(code_1=status_code_obj["1"],
                           code_2=int(status_code_obj["2"]) - 1 if int(status_code_obj["2"]) > 0 else 0,
                           code_3=status_code_obj["3"], code_4=status_code_obj["4"], code_5=status_code_obj["5"])
    try:
        cdb.insert([http_obj])
    except Exception as e:
        logger.error(e)


def save_site_database(data_site):
    date = get_current_time()
    print("save_site: ", date, data_site)
    cdb = ClickhouseBase()
    # Update thong tin web connection
    for site_obj in data_site:
        web_connect = MonitorSiteConnection(site_connect=site_obj,
                                            request_site=data_site[site_obj])
        try:
            cdb.insert([web_connect])
        except Exception as e:
            logger.error(e)


def save_ip_database(data_ip):
    date = get_current_time()
    print("save_ip: ", date, data_ip)
    cdb = ClickhouseBase()
    # Update thong tin IP connection
    for ip in data_ip:
        ip_connect = MonitorIPConnection(ip_connect=ip,
                                         request_ip=data_ip[ip])
        try:
            cdb.insert([ip_connect])
        except Exception as e:
            logger.error(e)


def process_log(new_logs):
    try:
        list_log_data = process_log_to_info(new_logs)
        status_obj = {}
        site_obj = {}
        ip_obj = {}
        if len(list_log_data) > 0:
            status_obj = count_status_code(list_log_data)
            site_obj = count_site_connect(list_log_data)
            ip_obj = count_ip_connect(list_log_data)
        save_to_database(status_obj)
        save_site_database(site_obj)
        save_ip_database(ip_obj)

        return True
    except Exception as e:
        logger.error(e)
        return False


def main():
    print("Monitor http status")
    #############################################
    log_file = open(LOG_FILE_DIR, 'r')
    log_file.seek(0, 2)
    last_size = log_file.tell()
    log_file.close()
    while True:
        log_file = open(LOG_FILE_DIR, 'r')
        log_file.seek(0, 2)
        current_size = log_file.tell()
        if current_size > last_size:
            logger.debug(f"New log entry {get_current_time()}")
            log_file.seek(last_size)
            block_size = current_size - last_size
            new_logs = log_file.read(block_size)
            if process_log(new_logs):
                last_size = current_size
        elif current_size < last_size:
            last_size = 0
        else:
            logger.debug("No new log entry")
        log_file.close()
        time.sleep(10)
    ##############################################

    # with open(LOG_FILE_DIR, 'r') as log_file:
    #     log_data = log_file.read()
    # process_log(log_data)


if __name__ == '__main__':
    logger = c_logger(MONITOR_LOG_DIR + '/monitor-http-status-service.log').log_writer
    while not check_database_available():
        logger.error("Database not available yet")
        time.sleep(1)
    main()
