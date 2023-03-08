from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .config_rule_core import ConFigRule


class ConFigRuleAPI(Resource):
    def __init__(self):
        self.application = ConFigRule()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.application.get_all_rules(http_parameters)

    @jwt_required
    def post(self):
        json_data = request.get_json()
        return self.application.add_new_rule(json_data)


class ConFigRuleDetailAPI(Resource):
    def __init__(self):
        self.application = ConFigRule()

    @jwt_required
    def get(self, rule_id):
        return self.application.get_rule_detail(rule_id)

    @jwt_required
    def put(self, rule_id):
        json_data = request.get_json()
        return self.application.edit_a_rule(rule_id, json_data)

    @jwt_required
    def delete(self, rule_id):
        return self.application.delete_rule(rule_id)
