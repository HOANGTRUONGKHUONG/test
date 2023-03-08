from flask import request
from flask_jwt_extended import jwt_required

from app.functions.monitors.ddos.monitor_ddos_core import MonitorDdosApp, MonitorDdosNet
from app.functions.monitors.monitor_api import MonitorAPI, MonitorChartAPI, MonitorChartCountAPI, MonitorDownload
from app.libraries.data_format.http_parameters_replace import replace_param


class MonitorDdosAppAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorDdosApp)

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        # reformat http param because FE pass wrong param
        replace_param(http_parameters, 'attacker_ip', 'ip_address')
        replace_param(http_parameters, 'group_rule', 'rule')
        return self.monitor.get_information(http_parameters)


class UnlockAppIPAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorDdosApp)

    @jwt_required
    def put(self):
        json_data = request.get_json()
        return self.monitor.put_to_unlock_ip(json_data)


class MonitorDDoSChartAPI(MonitorChartAPI):
    def __init__(self):
        super().__init__(MonitorDdosApp)


class MonitorDDoSChartCountAPI(MonitorChartCountAPI):
    def __init__(self):
        super().__init__(MonitorDdosApp)


class MonitorDDosAppDownload(MonitorDownload):
    def __init__(self):
        super().__init__(MonitorDdosApp)


class MonitorDdosNetAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorDdosNet)

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        # reformat http param because FE pass wrong param
        replace_param(http_parameters, 'attacker_ip', 'ip_address')
        replace_param(http_parameters, 'group_rule', 'rule')
        return self.monitor.get_information(http_parameters)


class MonitorDDosNetDownload(MonitorDownload):
    def __init__(self):
        super().__init__(MonitorDdosNet)


class UnlockNetIPAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorDdosNet)

    @jwt_required
    def put(self):
        json_data = request.get_json()
        return self.monitor.put_to_unlock_ip(json_data)
