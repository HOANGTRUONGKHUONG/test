from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .service_collections import ServiceCollections
from .service_core import ServiceConfiguration


class ServiceAPI(Resource):
    def __init__(self):
        self.service = ServiceConfiguration()
        self.service_collections = ServiceCollections()

    @jwt_required
    def get(self, interface_name):
        http_parameters = request.args.to_dict()
        # outsource not pass limit page -> generate limit page
        if "limit" not in http_parameters:
            http_parameters["limit"] = 100
        if "offset" not in http_parameters:
            http_parameters["offset"] = 0
        return self.service.get_all_service(interface_name, http_parameters)

    @jwt_required
    def post(self, interface_name):
        json_data = request.get_json()
        return self.service.allow_service(interface_name, json_data)

    def options(self, interface_name):
        return self.service_collections.service_access_collections()


class ServiceDetailAPI(Resource):
    def __init__(self):
        self.service = ServiceConfiguration()

    @jwt_required
    def get(self, service_id):
        return self.service.get_service_detail(service_id)

    @jwt_required
    def put(self, service_id):
        json_data = request.get_json()
        return self.service.edit_service(service_id, json_data)

    @jwt_required
    def delete(self, service_id):
        return self.service.delete_service(service_id)
