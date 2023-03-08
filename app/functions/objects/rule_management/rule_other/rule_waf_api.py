from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .rule_waf_core import WafRule

class WafRuleAPI(Resource):
	def  __init__(self):
		self.waf_rule = WafRule()

	@jwt_required
	def get(self, waf_rule_id):
		http_parameters = request.args.to_dict()
		return self.waf_rule.get_all_rule(http_parameters, waf_rule_id)

	@jwt_required
	def post(self, waf_rule_id):
		rule_json_data = request.get_json()
		return self.waf_rule.add_new_rule(rule_json_data, waf_rule_id)

	
class WafRuleDetailAPI(Resource):
	def __init__(self):
		self.waf_rule = WafRule()

	@jwt_required
	def get(self, rule_id, waf_rule_id):
		return self.waf_rule.get_rule_detail(rule_id, waf_rule_id)

	@jwt_required
	def put(self, rule_id, waf_rule_id):
		rule_json_data = request.get_json()
		return self.waf_rule.edit_rule(rule_json_data, rule_id, waf_rule_id)
               

	@jwt_required
	def delete(self, rule_id, waf_rule_id):
		return self.waf_rule.delete_rule(rule_id, waf_rule_id)