from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.validate_data import is_domain, is_true_datetime_format
from app.libraries.http.response import get_status_code_200, status_code_200, status_code_400, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.libraries.system.shell import run_command
from app.libraries.system.sys_time import get_current_time, datetime_to_str


def verify_json_data(json_data):
    verify = ""
    import pytz
    list_timezone = pytz.common_timezones
    if "timezone" in json_data:
        if json_data["timezone"] not in list_timezone:
            verify += "timezone not validate, "
    if "server" in json_data:
        if not is_domain(json_data["server"]):
            verify += "ntp server is not validate, "
    if "datetime" in json_data:
        if not is_true_datetime_format(json_data["datetime"]):
            verify += "datetime not validate, "
    return verify


class SystemTimeConfiguration(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("system_time_config").log_writer

    def get_current_setting(self):
        return get_status_code_200(self.read_system_config())

    def change_system_setting(self, json_data):
        # set time and timezone
        run_command("systemctl stop systemd-timesyncd")
        output_set_timezone = run_command(f"timedatectl set-timezone {json_data['timezone']}")
        set_datetime = f"timedatectl set-time '{json_data['datetime']}'"
        output_set_datetime = run_command(set_datetime)
        # set ntp server
        if "server" in json_data:
            run_command(f"bash -c 'echo server {json_data['server']} prefer iburst >> /etc/ntp.conf'")
        self.session.close()
        self.engine_connect.dispose()
        monitor_setting = log_setting(action="System time", status=1, description="Change system time")
        return status_code_200("put.system.time.success", self.read_system_config())

    def get_time_from_ntp(self, http_parameters):
        import ntplib
        from time import ctime
        c = ntplib.NTPClient()
        try:
            response = c.request(http_parameters["server"], version=3)
            from datetime import datetime
            datetime_data = datetime.strptime(ctime(response.tx_time), '%a %b %d %X %Y')
            data = {
                "timezone": http_parameters["timezone"],
                "server": http_parameters["server"],
                "datetime": datetime_to_str(datetime_data)
            }
            return status_code_200("get.system.time.ntp.success", data)
        except Exception as e:
            self.logger.error(e)
            return status_code_400("get.system.time.ntp.fail.client")
        finally:
            self.session.close()
            self.engine_connect.dispose()

    def get_list_timezone(self):
        import pytz
        try:
            list_timezone = pytz.common_timezones
            return get_status_code_200(list_timezone)
        except Exception as e:
            self.logger.error(e)
            return status_code_500("get.timezone.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()

    def read_system_config(self):
        import re
        with open("/etc/timezone") as f:
            timezone = f.read().rstrip()
        with open("/etc/ntp.conf") as f:
            regex = re.compile(r"server "
                               r"(?P<ntp_server>(?:[a-z0-9](?:[a-z0-9-]{0,61}"
                               r"[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]) "
                               r"prefer iburst")
            server = [m.groupdict() for m in regex.finditer(f.read())]
        if len(server) > 0:
            ntp_server = server[len(server) - 1]["ntp_server"]
        else:
            ntp_server = None
        system_time_obj = {
            "timezone": timezone,
            "ntp_server": ntp_server,
            "datetime": get_current_time()
        }
        return system_time_obj
