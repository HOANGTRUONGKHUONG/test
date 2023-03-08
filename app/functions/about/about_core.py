from datetime import timedelta

import cpuinfo
from psutil import virtual_memory

from app.libraries.http.response import get_status_code_200


class About(object):
    def __init__(self):
        pass

    def read_system_information(self, http_parameters):
        cpu_name = cpuinfo.get_cpu_info()['brand_raw']
        ram_total = f"{round(virtual_memory().total / (1024.0 ** 3), 0)} GB"
        # read system uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_string = str(timedelta(seconds=uptime_seconds))
        return get_status_code_200({
            "system_cpu": cpu_name,
            "system_ram": ram_total,
            "system_uptime": uptime_string,
            "firmware_version": "1.0.0"
        })

    def set_system_name(self, json_data):
        pass
