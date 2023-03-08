from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .ddos_network_layer_core import DdosNetworkLayer


class DDosNetworkLayerAPI(Resource):
    def __init__(self):
        self.net = DdosNetworkLayer()

    @jwt_required
    def get(self):
        return self.net.get_all_rule()


class DDosNetworkLayerDetailAPI(Resource):
    def __init__(self):
        self.net = DdosNetworkLayer()

    @jwt_required
    def get(self, rule_id):
        return self.net.get_rule_detail(rule_id)

    @jwt_required
    def put(self, rule_id):
        json_data = request.get_json()
        return self.net.edit_rule(rule_id, json_data)
