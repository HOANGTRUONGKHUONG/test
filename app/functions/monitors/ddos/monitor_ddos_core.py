from logging import Logger

from app.functions.monitors.monitor import Monitor
from app.libraries.data_format.monitor_chart import group_data_by_hour, get_monitor_data_chart
from app.libraries.http.response import get_status_code_200, status_code_400
from app.libraries.system.sys_time import datetime_to_str
from app.model.ClickhouseModel import MonitorDdosApplication, MonitorDdosNetwork


class MonitorDdosNet(Monitor):
    def __init__(self):
        log = Logger("monitor_ddos_net")
        super().__init__(log, MonitorDdosNetwork)

    def get_base_item(self, item):
        base_item = {
            "ip_addr": item.ip_address,
            "block_time": datetime_to_str(item.datetime),
            "country": item.attacker_country,
            "rule": item.rule,
            "unlock": item.unlock,
            "detail": item.detail
        }
        return base_item


class MonitorDdosApp(Monitor):
    def __init__(self):
        log = Logger("monitor_ddos_app")
        super().__init__(log, MonitorDdosApplication)

    def get_base_item(self, item):
        base_item = {
            "ip_addr": item.ip_address,
            "block_time": datetime_to_str(item.datetime),
            "country": item.attacker_country,
            "rule": item.rule,
            "website": item.website_domain,
            "unlock": item.unlock,
            "detail": item.detail
        }
        return base_item

    def get_monitor_chart(self, http_parameters):
        if "attacker_country" in http_parameters:
            column = "attacker_country"
        elif "websites" in http_parameters:
            column = "website_domain"
            http_parameters["website_domain"] = http_parameters["websites"]
        # top 10 ip DDoS.
        elif "ip_address" in http_parameters:
            column = "ip_address"
            http_parameters["ip_address"] = http_parameters["ip_address"]
        else:
            return status_code_400("get.ddos.monitor.chart.fail.client")
        chart_data = get_monitor_data_chart(self.db, MonitorDdosApplication, column, http_parameters,
                                            self.logger)
        return get_status_code_200({"data": chart_data})

    def get_monitor_count_chart(self):
        monitor_data = group_data_by_hour(self.db, MonitorDdosApplication)
        return get_status_code_200({"data": monitor_data})
