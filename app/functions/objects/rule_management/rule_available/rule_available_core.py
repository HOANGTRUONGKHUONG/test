from app.libraries.ORMBase import  ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.configuration.web_server import ngx_reload
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import RuleAvailableBase


def verify_json_data(json_data):
    verify = ""
    if "rule_available_status" in json_data:
        if json_data["rule_available_status"] not in [1, 0]:
            verify += f"rule_available_status {json_data['rule_available_status']} not validate, "

    return verify

class RuleAvailable(object):
	def __init__(self):
		self.session, self.engine_connect = ORMSession_alter()
		self.logger = c_logger("rule_available")

	def get_all_rule_available(self):
		list_rule_id = self.session.query(RuleAvailableBase).all()
		print("nghi:  ", type(list_rule_id))

		all_rule_available_base_data = []
		for rule in list_rule_id:
			all_rule_available_base_data.append(self.read_rule_available_detail(rule.id))
		self.session.close()
		self.engine_connect.dispose()
		return get_status_code_200(all_rule_available_base_data)


	def get_rule_available_detail(self, rule_available_id):
		rule_detail = self.read_rule_available_detail(rule_available_id)
		self.session.close()
		self.engine_connect.dispose()
		if bool(rule_detail):
			return status_code_200("get.rule.available.detail.success", rule_detail)
		else:
			return status_code_400("get.rule.available.detail.fail.client")
	
	def change_rule_available_status(self, json_data, rule_available_id):
		error_code = verify_json_data(json_data)
		if error_code != "":
			self.logger.error(error_code)
			self.session.close()
			monitor_setting = log_setting("Rule Available", 0, "Verify input not satisfied")
			return status_code_400("put.rule.available.status.fail.client")

		rule_available_detail = self.read_rule_available_detail(rule_available_id)
  
		if not bool(rule_available_detail):
			self.session.close()
			monitor_setting = log_setting("Rule Available", 0, "Condition is not satisfied")
			return status_code_400("put.rule.available.status.fail.client")

		self.session.query(RuleAvailableBase). \
			filter(RuleAvailableBase.id.__eq__(rule_available_id)).update({"rule_available_status": json_data["rule_available_status"]})
		try:
			self.session.commit()
			monitor_setting = log_setting(action="Rule Available", status=1, description="Change rule available status")
			ngx_reload()
			return status_code_200("put.rule.available.status.success", self.read_rule_available_detail(rule_available_id))
		except Exception as e:
			self.logger.error(f"Change rule available status {rule_available_id} fail, {e}")
			self.session.rollback()
		finally:
			self.session.close()
			self.engine_connect.dispose()
		monitor_setting = log_setting(action="Rule Available", status=0, description=f"Change rule available status failed {e}")
		return status_code_500("put.rule.available.status.fail.server")

	def read_rule_available_detail(self, rule_available_id):
		rule_available_detail = self.session.query(RuleAvailableBase).filter(RuleAvailableBase.id.__eq__(rule_available_id)).first()
		if rule_available_detail:
			rule_available_detail_data = {
				"id" : rule_available_detail.id,
				"rule_available_name": rule_available_detail.rule_available_name,
				"rule_available_status": rule_available_detail.rule_available_status
			}
			return rule_available_detail_data
		else:
			self.session.close()
			self.engine_connect.dispose()
			return {}

	