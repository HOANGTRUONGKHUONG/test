from app.functions.monitors.monitor import Monitor
from app.libraries.data_format.monitor_chart import group_data_by_hour, get_monitor_data_chart
from app.libraries.data_format.string_format import string_to_json
from app.libraries.http.response import get_status_code_200, status_code_400
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorWAF as MonitorWAFBase


class MonitorWAF(Monitor):
    def __init__(self):
        self.logger = c_logger("monitor_waf")
        super().__init__(self.logger.log_writer, MonitorWAFBase)

    def get_base_item(self, item):
        base_item = {
            "attacker_ip": (f"{item.attacker_ip}: {item.attacker_port}"),
            "attacker_country": item.attacker_country,
            "datetime": datetime_to_str(item.datetime),
            "group_rule": item.rule_id,
            "group_website": item.group_website,
            "website_domain": item.website_domain,
            "request_header": string_to_json(item.request_header),
            "violation_code": item.violation_code,
            "matched_info": (f"{item.matched_info} status: {item.resp_status}" )
        }
        return base_item

    def get_monitor_chart(self, http_parameters):
        if "attacker_country" in http_parameters:
            column = "attacker_country"
        elif "attacker_ip" in http_parameters:
            column = "attacker_ip"
        elif "website_domain" in http_parameters:
            column = "website_domain"
        elif "group_rule" in http_parameters:
            column = "group_rule"
        else:
            return status_code_400("get.waf.monitor.chart.fail.client")
        chart_data = get_monitor_data_chart(self.db, MonitorWAFBase, column, http_parameters, self.logger)
        return get_status_code_200({"data": chart_data})

    def get_monitor_count_chart(self):
        monitor_data = group_data_by_hour(self.db, MonitorWAFBase)
        return get_status_code_200({"data": monitor_data})
