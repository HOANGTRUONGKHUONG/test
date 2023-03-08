from abc import ABC, abstractmethod

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.configuration.firewall import delete_ip_in_ips_chain
from app.libraries.data_format.clickhouse_helper import get_data_table
from app.libraries.data_format.paging import reformat_data_with_paging, get_average_data
from app.libraries.http.file_export import monitor_export_data
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_500
from app.libraries.system.sys_time import datetime_to_str


class Monitor(ABC):
    @abstractmethod
    def __init__(self, log, monitor_base, list_param=None):
        if list_param is None:
            list_param = []
        self.logger = log
        self.db = ClickhouseBase()
        self.monitor_base = monitor_base
        # list_param is column of table need to calculate avg when select long time
        # and return a number of value, not all
        self.list_param = list_param

    def get_base_item(self, item):
        pass

    def download_log(self, http_parameters):
        list_item, number_of_value = get_data_table(self.db, self.logger, http_parameters, self.monitor_base)
        all_base_data = self.extract_value(list_item)
        return monitor_export_data(all_base_data)

    def get_information(self, http_parameters):
        # check if list param have been init
        # table have list_param is table need to calculate average value (resource, traffic, ...)
        if not bool(self.list_param):
            if "avg_value" in http_parameters:
                del http_parameters["avg_value"]
        list_item, number_of_value = get_data_table(self.db, self.logger, http_parameters, self.monitor_base)
        if "avg_value" in http_parameters:
            all_base_data = get_average_data(self.extract_value(list_item), http_parameters["avg_value"],
                                             self.list_param)
            http_parameters["limit"] = http_parameters["avg_value"]
            number_of_value = len(all_base_data)
        else:
            all_base_data = self.extract_value(list_item)

        return get_status_code_200(
            reformat_data_with_paging(all_base_data, number_of_value,
                                      int(http_parameters["limit"]), int(http_parameters["offset"]))
        )

    def extract_value(self, list_item):
        _all_base_data = []
        for item in list_item:
            base_item = self.get_base_item(item)
            _all_base_data.append(base_item)
        return _all_base_data

    def get_monitor_chart(self, http_parameters):
        pass

    def get_monitor_count_chart(self):
        pass

    def put_to_unlock_ip(self, json_data):
        ip_obj = self.monitor_base.objects_in(self.db). \
            filter(self.monitor_base.ip_address.__eq__(json_data["ip_addr"]),
                   self.monitor_base.datetime.__eq__(json_data["block_time"]),
                   self.monitor_base.unlock.__eq__(0))
        if ip_obj:
            if delete_ip_in_ips_chain(json_data['ip_addr']):
                self.logger.info("Update rule success")
                data = []
                for obj in ip_obj:
                    data = {
                        "ip_addr": obj.ip_address,
                        "block_time": datetime_to_str(obj.datetime),
                        "country": obj.attacker_country,
                        "rule": obj.rule,
                        "website": obj.website_domain,
                        "unlock": 1,
                        "detail": obj.detail
                    }
                    ip_obj.update(unlock=1)
                return get_status_code_200(data)
            else:
                self.logger.info(f"Update rule failed")
                return status_code_500("Update rule fail server")
        else:
            self.logger.error("No IP")
            return status_code_400("unlock ip fail client")
