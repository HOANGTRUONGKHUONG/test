from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .trustwave_core import TrustwaveRule

class TrustwaveRuleAPI(Resource):
    def __init__(self):
        self.trustwave_rule = TrustwaveRule()
        
    @jwt_required
    def get(self, rule_available_id):
        http_parameters = request.args.to_dict()
        return self.trustwave_rule.get_all_trustwave_rule(http_parameters, rule_available_id)

	
class TrustwaveRuleDetailAPI(Resource):
    def __init__(self):
        self.trustwave_rule = TrustwaveRule()
        
    @jwt_required
    def get(self, rule_available_id, trustwave_id):
        return self.trustwave_rule.get_trustwave_rule_detail(trustwave_id, rule_available_id)
    
    @jwt_required
    def put(self, trustwave_id, rule_available_id):
        json_data = request.get_json()
        return self.trustwave_rule.edit_trustwave_rule(json_data, trustwave_id, rule_available_id) 

	
class DownloadTrustwaveRule(Resource):
    def __init__(self):
        self.trustwave_rule = TrustwaveRule()
        
    @jwt_required
    def get(self):
        return self.trustwave_rule.download()