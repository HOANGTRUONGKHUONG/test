from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.firewall import run_config_rule
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import DDosNetworkLayerBase


class DdosNetworkLayer(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("Ddos_network_layer")

    def get_all_rule(self):
        list_rule = self.session.query(DDosNetworkLayerBase.id).all()
        all_uri_base_data = []
        for uri in list_rule:
            all_uri_base_data.append(self.read_rule_detail(uri.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200({"data": all_uri_base_data})

    def get_rule_detail(self, rule_id):
        rule_detail = self.read_rule_detail(rule_id)
        if bool(rule_detail):
            return status_code_200("get.rule.success", rule_detail)
        else:
            return status_code_400("get.rule.fail.client")

    def edit_rule(self, rule_id, json_data):
        rule_detail = self.read_rule_detail(rule_id)
        rule_detail.update(json_data)
        rule_obj = self.session.query(DDosNetworkLayerBase).filter(DDosNetworkLayerBase.id.__eq__(rule_id)).one()
        rule_obj.name = rule_detail["name"]
        rule_obj.threshold = rule_detail["threshold"]
        rule_obj.duration = rule_detail["duration"]
        rule_obj.block_duration = rule_detail["block_duration"]
        rule_obj.state = rule_detail["state"]
        rule_obj.alert = rule_detail["alert"]
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting("Network rule", 1, "Edit rule")
        except Exception as e:
            self.logger.log_writer.error(f"Edit rule fail, {e}")
            monitor_setting = log_setting("Network rule", 0, "Edit rule failed")
            return status_code_500("put.rule.fail.client")
        run_config_rule()
        data = self.read_rule_detail(rule_id)
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("put.rule.success", data)

    def read_rule_detail(self, rule_id):
        rule_detail = self.session.query(DDosNetworkLayerBase).filter(DDosNetworkLayerBase.id.__eq__(rule_id)).first()
        if rule_detail:
            rule_base_data = {
                "id": rule_detail.id,
                "name": rule_detail.name,
                "threshold": rule_detail.threshold,
                "duration": rule_detail.duration,
                "block_duration": rule_detail.block_duration,
                "state": rule_detail.state,
                "alert": rule_detail.alert
            }
            return rule_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
