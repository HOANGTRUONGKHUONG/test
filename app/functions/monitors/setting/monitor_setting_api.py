from app.functions.monitors.monitor_api import MonitorAPI
from .monitor_setting_core import MonitorSetting
from flask_jwt_extended import jwt_required
from flask import request


class MonitorSettingAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorSetting)

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        if 'orderBy' not in http_parameters and 'orderType' not in http_parameters:
            http_parameters['orderBy'] = 'datetime'
            http_parameters['orderType'] = 'desc'
        return self.monitor.get_information(http_parameters)
