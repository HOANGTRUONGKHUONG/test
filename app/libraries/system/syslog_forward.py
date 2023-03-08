import logging
import os
import shutil
import time
import uuid
from logging.handlers import SysLogHandler
from socket import SOCK_DGRAM, SOCK_STREAM, gethostname

from app.libraries.inout.file import write_text_file
from app.libraries.system.shell import run_command
from app.setting import SYSTEM_ETC_DIR

RSYSLOG_BACKUP_DIR = os.path.join("tmp", "rsyslog_backup_config")
RSYSLOG_FORWARD_FILE = os.path.join(SYSTEM_ETC_DIR, "rsyslog.d", "69-forward.conf")


def config_forward_log(log_config):
    # log_config = {
    #     "log_file": {
    #         "modsecurity_log": {
    #             "file": "/var/log/nginx/modsec_audit.log"
    #         },
    #         "nginx_error_log": {
    #             "file": "/var/log/nginx/error.log"
    #         },
    #         "nginx_access_log": {
    #             "file": "/var/log/nginx/access.log"
    #         }
    #     },
    #     "syslog_server": {
    #         "ip_address": "192.168.10.130",
    #         "port": "514",
    #         "protocol": "udp",
    #         "facility": "kern",
    #         "severity": "warning"
    #     }
    # }
    config_string = "$ModLoad imfile"
    log_file = log_config["log_file"]
    remote_server = log_config['syslog_server']
    for log_type in log_file:
        config_string += f"""
$InputFileName {log_file[log_type]["file"]}
$InputFileTag {log_type}
$InputFileStateFile {log_type}
$InputFileSeverity {remote_server['severity']}
$InputFileFacility {remote_server['facility']}
$InputRunFileMonitor

"""
    config_string += f"{remote_server['facility']}.{remote_server['severity']} " \
                     f"{'@' if remote_server['protocol'] == 'udp' else '@@'}" \
                     f"[{remote_server['ip_address']}]:{remote_server['port']}"
    return write_text_file(RSYSLOG_FORWARD_FILE, config_string)


def forward_config_reader():
    def split_ip_port(ip_string):
        # [192.168.49.53]:514
        # [2001:db8:1f70::999:de8:7648:6e8]:514
        _ip_port = ip_string.split("]")
        _ip_address = _ip_port[0][1:]
        _port = _ip_port[1][1:]
        return [_ip_address, _port]

    # read current system forward config
    try:
        with open(RSYSLOG_FORWARD_FILE) as f:
            forward_config = f.readlines()
    except Exception as e:
        print(e)
        forward_config = []
    if len(forward_config) > 0:
        forward_location = ""
        for config_line in forward_config:
            if "@" in config_line:
                forward_location = config_line.rstrip()
                break

        [facility_severity, address] = forward_location.split(" ")
        [facility, severity] = facility_severity.split(".")
        if address.count("@") == 2:
            # tcp
            socket_type = SOCK_STREAM
            ip_port = address[2:]
        else:
            # udp
            socket_type = SOCK_DGRAM
            ip_port = address[1:]
        [ip_address, port] = split_ip_port(ip_port)
        log_type = []
        for config_line in forward_config:
            if "InputFileTag" in config_line:
                log_type.append(config_line.split(" ")[1].rstrip())
        return {
            "use_syslog_forward": True,
            "syslog_server_ip": ip_address,
            "syslog_server_port": port,
            "syslog_server_protocol": "tcp" if socket_type == SOCK_STREAM else "udp",
            "log_type": log_type,
            "facility": facility,
            "severity": severity,
        }
    else:
        return {
            "use_syslog_forward": False,
            "syslog_server_ip": None,
            "syslog_server_port": None,
            "syslog_server_protocol": None,
            "log_type": None,
            "facility": None,
            "severity": None
        }


def forward_config_remove():
    if os.path.isfile(RSYSLOG_FORWARD_FILE):
        os.remove(RSYSLOG_FORWARD_FILE)
    return True


def syslog_forward():
    def get_severity_level(level_name):
        level = {
            "crit": logging.CRITICAL,
            "error": logging.ERROR,
            "warning": logging.WARNING,
            "info": logging.INFO,
            "debug": logging.DEBUG
        }
        return level[level_name]

    forward_config = forward_config_reader()
    # create logger object
    logger = logging.getLogger(f'{gethostname()}_forward_log')
    logger.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)
    if forward_config["use_syslog_forward"]:
        if forward_config['facility'] in SysLogHandler.facility_names:
            facility_type = SysLogHandler.facility_names[forward_config['facility']]
        else:
            facility_type = SysLogHandler.facility_names['syslog']
        sh = SysLogHandler(address=(forward_config["syslog_server_ip"], int(forward_config["syslog_server_port"])),
                           facility=facility_type, socktype=forward_config["syslog_server_protocol"])
        sh.setLevel(get_severity_level(forward_config['severity']))
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger


def make_syslog_struct_from_dict(log_dict):
    result = f"{uuid.uuid1()} "
    for key in log_dict:
        result += f'{key}="{log_dict[key]}" '
    return f"{result}"


def rsyslog_backup():
    if os.path.exists(RSYSLOG_BACKUP_DIR):
        shutil.rmtree(RSYSLOG_BACKUP_DIR)
    shutil.copytree(os.path.join(SYSTEM_ETC_DIR, "rsyslog.d"), os.path.join(RSYSLOG_BACKUP_DIR, "rsyslog.d"))


def rsyslog_remove_backup():
    if os.path.exists(RSYSLOG_BACKUP_DIR):
        shutil.rmtree(RSYSLOG_BACKUP_DIR)


def rsyslog_rollback():
    backup_files = os.path.join(RSYSLOG_BACKUP_DIR, "rsyslog.d")
    for file_name in backup_files:
        full_file_name = os.path.join(backup_files, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, os.path.join(SYSTEM_ETC_DIR, "rsyslog.d"))


def rsyslog_apply_config():
    restart_message = run_command("service rsyslog stop")
    time.sleep(1)
    restart_message = run_command("service rsyslog start")
    return True


def rsyslog_check_config():
    check_config_message = run_command(f"{os.path.join('sbin', 'rsyslogd')} -N1")
    if "error" in str(check_config_message):
        return False
    return True


def rsyslog_push_test_message(log_config):
    # log_config = {
    #     "syslog_server": {
    #         "ip_address": "192.168.10.130",
    #         "port": "514",
    #         "protocol": "udp",
    #         "facility": "kern",
    #         "severity": "warning"
    #     }
    # }
    syslog_server = log_config["syslog_server"]
    command = f"/usr/bin/logger {'--tcp' if syslog_server['protocol'] == 'tcp' else '--udp'} " \
              f"--server {syslog_server['ip_address']} --port {syslog_server['port']} " \
              f"{syslog_server['facility']}.{syslog_server['severity']}_This_is_test_message"
    run_command(command)
    return True
