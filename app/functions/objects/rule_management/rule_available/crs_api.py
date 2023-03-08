from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .crs_core import CRSRule

class CRSRuleAPI(Resource):
	def  __init__(self):
		self.crs_rule = CRSRule()

	@jwt_required
	def get(self, rule_available_id):
		http_parameters = request.args.to_dict()
		return self.crs_rule.get_all_crs_rule(http_parameters, rule_available_id)

	
class CRSRuleDetailAPI(Resource):
	def __init__(self):
		self.crs_rule = CRSRule()

	@jwt_required
	def get(self, crs_id, rule_available_id):
		return self.crs_rule.get_crs_rule_detail(crs_id, rule_available_id)
		
	@jwt_required
	def put(self, crs_id, rule_available_id):
		json_data = request.get_json()
		return self.crs_rule.edit_crs_rule(json_data, crs_id, rule_available_id)   	

class DownloadCRSRule(Resource):
	def __init__(self):
		self.crs_rule = CRSRule()
  
	@jwt_required
	def get(self):
		return self.crs_rule.download()