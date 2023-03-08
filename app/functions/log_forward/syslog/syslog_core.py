from app.functions.log_forward.log_forward_collections import FACILITY_COLLECTIONS, SEVERITY_COLLECTIONS, \
    LOG_TYPE_COLLECTIONS
from app.libraries.data_format.validate_data import is_ipv4, is_ipv6, is_port
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.libraries.system.syslog_forward import forward_config_reader, rsyslog_backup, config_forward_log, \
    rsyslog_rollback, rsyslog_remove_backup, rsyslog_apply_config, forward_config_remove, rsyslog_check_config, \
    rsyslog_push_test_message


def key_in_object(_key, _object, list_value_check):
    if _key in _object:
        if isinstance(_object[_key], str):
            if _object[_key] not in list_value_check:
                return f"{_key}: {_object[_key]} not validate, "
        if isinstance(_object[_key], list):
            for value in _object[_key]:
                if value not in list_value_check:
                    return f"{_key}: {value} not validate, "
        if isinstance(_object[_key], int):
            if _object[_key] not in list_value_check:
                return f"{_key}: {_object[_key]} not validate, "
        return ""
    else:
        return f"{_key} not exist"


def get_list_from_object(_object):
    _list_key = []
    for _key in _object:
        _list_key.append(_key)
    return _list_key


def verify_json_data(json_data):
    verify = ""
    verify += key_in_object("config_status", json_data, [1, 0])
    verify += key_in_object("protocol", json_data, ["tcp", "udp"])
    verify += key_in_object("facility", json_data, get_list_from_object(FACILITY_COLLECTIONS))
    verify += key_in_object("severity", json_data, get_list_from_object(SEVERITY_COLLECTIONS))
    verify += key_in_object("log_type", json_data, get_list_from_object(LOG_TYPE_COLLECTIONS))

    if "ip_domain" in json_data:
        ip_domain = json_data["ip_domain"]
        if not is_ipv4(str(ip_domain)) and not is_ipv6(str(ip_domain)):
            verify += f"ip {ip_domain} is not true, "

    if "port" in json_data:
        port = json_data["port"]
        if not is_port(str(port)):
            verify += f"{port} is not true, "
    return verify


class SyslogForward(object):
    def __init__(self):
        self.logger = c_logger("syslog_forward")

    def current_config_reader(self):
        current_config = forward_config_reader()
        syslog_config = {
            "config_status": 1 if current_config["use_syslog_forward"] else 0,
            "ip_domain": current_config["syslog_server_ip"],
            "port": current_config["syslog_server_port"],
            "facility": current_config["facility"],
            "severity": current_config["severity"],
            "protocol": current_config["syslog_server_protocol"],
            "log_type": current_config["log_type"]
        }
        return syslog_config

    def read_config(self):
        syslog_config = self.current_config_reader()
        return get_status_code_200(syslog_config)

    def change_config(self, json_data):
        json_error = verify_json_data(json_data)
        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("post.logforward.fail.client")
        rsyslog_backup()
        log_files = {}
        for log_type in json_data["log_type"]:
            log_files[log_type] = LOG_TYPE_COLLECTIONS[log_type]
        log_config = {
            "log_file": log_files,
            "syslog_server": {
                "ip_address": json_data["ip_domain"],
                "port": json_data["port"],
                "protocol": json_data["protocol"],
                "facility": json_data["facility"],
                "severity": json_data["severity"]
            }
        }
        config_forward_log(log_config)

        if rsyslog_check_config():
            # action_status = log_setting(action="Log Forward", status=1, description="Config Log Forward")
            rsyslog_apply_config()
            rsyslog_remove_backup()
            return status_code_200("post.logforward.success", self.current_config_reader())
        rsyslog_rollback()
        # action_status = log_setting(action="Log Forward", status=0, description="Config Log Forward")
        return status_code_500("post.logforward.fail.server")

    def remove_config(self):
        rsyslog_backup()
        forward_config_remove()
        if rsyslog_check_config():
            # action_status = log_setting(action="Log Forward", status=1, description="Remove Log Forward")
            rsyslog_apply_config()
            rsyslog_remove_backup()
            return status_code_200("delete.logforward.success", {})
        rsyslog_rollback()
        # action_status = log_setting(action="Log Forward", status=0, description="Remove Log Forward")
        return status_code_500("delete.logforward.fail.server")

    def test_connection(self, json_data):
        def verify_test(json_data):
            verify = ""
            if "ip_domain" in json_data:
                ip_domain = json_data["ip_domain"]
                if not is_ipv4(str(ip_domain)) and not is_ipv6(str(ip_domain)):
                    verify += f"ip {ip_domain} is not true, "

            verify += key_in_object("protocol", json_data, ["tcp", "udp"])

            if "port" in json_data:
                port = json_data["port"]
                if not is_port(str(port)):
                    verify += f"{port} is not true, "
            return verify

        json_error = verify_test(json_data)

        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("post.logforward.test.fail.client")
        log_config = {
            "syslog_server": {
                "ip_address": json_data["ip_domain"],
                "port": json_data["port"],
                "protocol": json_data["protocol"],
                "facility": "user",
                "severity": "debug"
            }
        }
        rsyslog_push_test_message(log_config)
        return status_code_200("post.logforward.test.success", {})
