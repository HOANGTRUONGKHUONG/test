from flask import request
from flask_restful import Resource

from .system_status_core import SystemStatus


class SystemStatusAPI(Resource):
    def __init__(self):
        self.system = SystemStatus()

    def post(self):
        json_data = request.get_json()
        return self.system.reboot(json_data)
