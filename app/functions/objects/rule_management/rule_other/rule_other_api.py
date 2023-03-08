from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .rule_other_core import RuleOther

class RuleOtherAPI(Resource):
	def  __init__(self):
		self.rule_other = RuleOther()

	@jwt_required
	def get(self):
		http_parameters = request.args.to_dict()
		return self.rule_other.get_all_rule_other(http_parameters)

	@jwt_required
	def post(self):
		other_rule_json_data = request.get_json()
		return self.rule_other.add_new_rule_other(other_rule_json_data)

	
class RuleOtherDetailAPI(Resource):
	def __init__(self):
		self.rule_other = RuleOther()

	@jwt_required
	def get(self, waf_rule_id):
		return self.rule_other.get_rule_other_detail(waf_rule_id)

	@jwt_required
	def put(self, waf_rule_id):
		other_rule_json_data = request.get_json()
		return self.rule_other.edit_rule_other(waf_rule_id, other_rule_json_data)
               

	@jwt_required
	def delete(self, waf_rule_id):
		return self.rule_other.delete_rule_other(waf_rule_id)

class DownloadRuleOther(Resource):
	def __init__(self):
		self.down = RuleOther()

	@jwt_required
	def get(self, waf_rule_id):
		return self.down.download_rule(waf_rule_id)

class UploadRuleOther(Resource):
	def __init__(self):
		self.up = RuleOther()

	@jwt_required
	def post(self, waf_rule_id):
		return self.up.upload_rule(request, waf_rule_id)