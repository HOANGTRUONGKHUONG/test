from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .rule_available_core import RuleAvailable

class RuleAvailableAPI(Resource):
	def  __init__(self):
		self.rule_available = RuleAvailable()

	@jwt_required
	def get(self):
		# http_parameters = request.args.to_dict()
		return self.rule_available.get_all_rule_available()

	
class RuleAvailableDetailAPI(Resource):
	def __init__(self):
		self.rule_available = RuleAvailable()

	@jwt_required
	def get(self, rule_available_id):
		return self.rule_available.get_rule_available_detail(rule_available_id)	

	@jwt_required
	def put(self, rule_available_id):
		json_data = request.get_json()
		return self.rule_available.change_rule_available_status(json_data, rule_available_id)


class DownloadRuleAvailable(Resource):
	def __init__(self):
		self.down = RuleAvailable()

	@jwt_required
	def get(self):
		return self.down.download_rule()