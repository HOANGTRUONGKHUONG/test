from abc import abstractmethod

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import edit_role_require


class IpAPI(Resource):
    @abstractmethod
    def __init__(self, ip_core):
        self.ip = ip_core()

    @jwt_required
    def get(self):
        http_parameter = request.args.to_dict()
        return self.ip.get_list(http_parameter)

    @edit_role_require
    def post(self):
        json_data = request.get_json()
        return self.ip.add_new_ip(json_data)


class IpDetailAPI(Resource):
    @abstractmethod
    def __init__(self, ip_core):
        self.ip = ip_core()

    @jwt_required
    def get(self, ip_id):
        return self.ip.get_detail_ip(ip_id)

    @edit_role_require
    def put(self, ip_id):
        json_data = request.get_json()
        return self.ip.edit_ip(ip_id, json_data)

    @edit_role_require
    def delete(self, ip_id):
        return self.ip.delete_ip(ip_id)
