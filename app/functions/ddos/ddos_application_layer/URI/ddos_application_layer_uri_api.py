from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .ddos_application_layer_uri_core import DDosApplicationUri


class DDosApplicationURIAPI(Resource):
    def __init__(self):
        self.uri = DDosApplicationUri()

    @jwt_required
    def get(self, rule_id):
        return self.uri.get_all_uri(rule_id)


class DDosApplicationURIDetailAPI(Resource):
    def __init__(self):
        self.uri = DDosApplicationUri()

    @jwt_required
    def delete(self, rule_id):
        return self.uri.delete_uri(rule_id)
