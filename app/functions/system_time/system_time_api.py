from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .system_time_core import SystemTimeConfiguration


class SystemTimeAPI(Resource):
    def __init__(self):
        self.time = SystemTimeConfiguration()

    @jwt_required
    def get(self):
        return self.time.get_current_setting()

    @jwt_required
    def post(self):
        json_data = request.get_json()
        return self.time.change_system_setting(json_data)


class SystemNTPTimeAPI(Resource):
    def __init__(self):
        self.time = SystemTimeConfiguration()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.time.get_time_from_ntp(http_parameters)


class TimezoneAPI(Resource):
    def __init__(self):
        self.time = SystemTimeConfiguration()

    @jwt_required
    def get(self):
        return self.time.get_list_timezone()
