from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .ssl_core import SSL


class SSLAPI(Resource):
    def __init__(self):
        self.ssl = SSL()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.ssl.get_all_ssl(http_parameters)

    @jwt_required
    def post(self):
        ssl_json_data = request.get_json()
        return self.ssl.create_new_ssl(ssl_json_data)


class SSLDetailAPI(Resource):
    def __init__(self):
        self.ssl = SSL()

    @jwt_required
    def get(self, ssl_id):
        return self.ssl.get_ssl_detail(ssl_id)

    @jwt_required
    def put(self, ssl_id):
        ssl_json_data = request.get_json()
        return self.ssl.edit_ssl(ssl_id, ssl_json_data)

    @jwt_required
    def delete(self, ssl_id):
        return self.ssl.delete_ssl(ssl_id)
