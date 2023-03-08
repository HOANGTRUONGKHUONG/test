from sqlalchemy import or_
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_default_value, advanced_filter
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import RuleOtherDetailBase, RuleOtherBase
import os
import msc_pyparser

def verify_input(rule_json_data):
    verify = ""
    # check length description
    if "description" in rule_json_data and len(rule_json_data["description"]) > 500:
        verify += "description too long, " 


    return verify

class WafRule(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("rule_waf")

    def get_all_rule(self, http_parameters, waf_rule_id):
      #  self.dong_bo_db_to_file(waf_rule_id)
        limit, offset, order = get_default_value(self.logger.log_writer, http_parameters, RuleOtherDetailBase)
        list_rule_detail_id = self.session.query(RuleOtherDetailBase.id).filter(RuleOtherDetailBase.waf_rule_id.__eq__(waf_rule_id))
    
       #  optional parameter
        if "search" in http_parameters:
            search_string = http_parameters["search"]
            base_column = list(RuleOtherDetailBase.__table__.columns)
            list_rule_detail_id = list_rule_detail_id.filter(
                or_(key.like(f"%{search_string}%") for key in base_column)
            )
        
        # filter
        list_rule_detail_id = advanced_filter(http_parameters, self.logger.log_writer, list_rule_detail_id, RuleOtherDetailBase)
        
        # get result
        list_rule_detail_id = list_rule_detail_id.group_by(RuleOtherDetailBase.id).order_by(order)

        # get final result
        number_of_rule_detail = list_rule_detail_id.count()
        list_rule_detail_id = list_rule_detail_id.limit(limit).offset(offset).all()

        # read result 
        all_rule_detail_base_data = []
        all_rule_detail_data = []
        for rule_waf in list_rule_detail_id:
            all_rule_detail_base_data.append(self.read_rule_detail(rule_waf.id, waf_rule_id))
            all_rule_detail_data = list(filter(None, all_rule_detail_base_data))
                       
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(all_rule_detail_data, number_of_rule_detail, 
                                      http_parameters["limit"], http_parameters["offset"]))


    def add_new_rule(self, rule_json_data, waf_rule_id):
        json_error = verify_input(rule_json_data)
        if json_error:
            print(json_error)
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("add.new.rule.fail.client")
        mparser = msc_pyparser.MSCParser()
        try:
            mparser.parser.parse(rule_json_data["rules"])
        except Exception as e:
            self.logger.log_writer.error(f"rule faild, {e}")
            return status_code_400("add.new.rule.fail.client")
        parsed = mparser.configlines
        for rules in parsed:
            if rules.get("type") == "SecRule" or rule.get("type") == "SecAction":
                rule = rules["actions"]
                list_file_rule = []
                rule_infor = {
                    "id_rule": "",
                    "msg": "",
                    "tag": []
                }
                for action in rule:
                    if action['act_name'] == "id":
                        rule_infor["id_rule"] = action['act_arg']
                    if action['act_name'] == "msg":
                        rule_infor["msg"] = action['act_arg']

                    if action['act_name'] == "tag":
                        rule_infor["tag"].append(action['act_arg'])

                list_file_rule.append(rule_infor)  
                tag_str = ",".join(tag for tag in rule_infor['tag'])
                list_rule_detail = self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).first()
                rule_id = list_rule_detail.id
                path_rule = f"/home/bwaf/modsec/rule_{rule_id}/rule_{rule_id}.conf"
                if self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.id_rule.__eq__(rule_infor["id_rule"])).first():
                    self.logger.log_writer.error(f"id rule trung, ")
                    return status_code_400("add.new.rule.fail.client")
                
                rule_obj = RuleOtherDetailBase(rules=rule_json_data["rules"],
                        description=rule_json_data["description"], waf_rule_id=waf_rule_id, id_rule=rule_infor["id_rule"], 
                        message=rule_infor["msg"], tag=tag_str, path_rule=path_rule)

                self.session.add(rule_obj)
                self.session.flush()
                try:
                    self.session.commit()
                    self.write_file(waf_rule_id)
                
                    data = self.read_rule_detail(rule_obj.id, waf_rule_id)
                    monitor_setting = log_setting("Rule waf ", 1, "Add new rule")
                except Exception as e:
                    monitor_setting = log_setting("Rule waf", 0, "Add new rule failed")
                    self.logger.log_writer.error(f"Add rule fail,{e}")
                    return status_code_500("post.rule.fail.server")
                finally:
                    self.session.close()
                    self.engine_connect.dispose()
                return status_code_200("post.rule.success", data)

    def get_rule_detail(self, rule_id, waf_rule_id):
     #   self.dong_bo_db_to_file(waf_rule_id)
        rule_detail = self.read_rule_detail(rule_id, waf_rule_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(rule_detail):
            return status_code_200("get.rule.success", rule_detail)
        else:
            return status_code_400("get.rule.fail.client")

    def edit_rule(self, rule_json_data, rule_id, waf_rule_id):
        json_error = verify_input(rule_json_data)
        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("put.rule.fail.client")
        mparser = msc_pyparser.MSCParser()
        try:
            mparser.parser.parse(rule_json_data["rules"])
        except Exception as e:
            self.logger.log_writer.error(f"rule faild, {e}")
            return status_code_400("put.rule.fail.client")
        parsed = mparser.configlines
        for rules in parsed:
            if rules.get("type") == "SecRule" or rule.get("type") == "SecAction":
                rule = rules["actions"]
                list_file_rule = []
                rule_detail = {
                    "id_rule": "",
                    "msg": "",
                    "tag": []
                }
                for action in rule:
                    if action['act_name'] == "id":
                        rule_detail["id_rule"] = action['act_arg']
                    if action['act_name'] == "msg":
                        rule_detail["msg"] = action['act_arg']

                    if action['act_name'] == "tag":
                        rule_detail["tag"].append(action['act_arg'])

                list_file_rule.append(rule_detail)  
                tag_str = ",".join(tag for tag in rule_detail['tag'])
                        
                if self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.id_rule.__eq__(rule_detail["id_rule"])).\
                    filter(RuleOtherDetailBase.id.__ne__(rule_id)).first():
                    self.logger.log_writer.error(f"id rule trung, ")
                    return status_code_400("put.rule.fail.client")

               # self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.id.__eq__(rule_id)).update(rule_json_data)
                self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.id.__eq__(rule_id)).update({"id_rule": rule_detail["id_rule"],
                                                                                                                "rules": rule_json_data["rules"],
                                                                                                                "description": rule_json_data["description"],
                                                                                                                "message": rule_detail["msg"],
                                                                                                                "tag": tag_str})
                try:
                    self.session.commit()
                    self.write_file(waf_rule_id)
                    monitor_setting = log_setting("Rule waf", 1, "Edit rule ")
                    data = self.read_rule_detail(rule_id, waf_rule_id)
                except Exception as e:
                    self.logger.log_writer.error(f"Edit rule fail, {e}")
                    monitor_setting = log_setting("Rule waf", 0, "Edit rule failed")
                    return status_code_500("put.rule.fail.server")
                finally:
                    self.session.close()
                    self.engine_connect.dispose()
                return status_code_200("put.rule.success", data)

    def delete_rule(self, rule_id, waf_rule_id):
        try:
            self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.waf_rule_id.__eq__(waf_rule_id)). \
                filter(RuleOtherDetailBase.id.__eq__(rule_id)).delete()
            try:
                self.session.commit()
                self.write_file(waf_rule_id)
                monitor_setting = log_setting("Rule waf", 1, "Delete rule waf")
            except Exception as e:
                self.logger.log_writer.error(f"Delete rule fail, {e}")
                monitor_setting = log_setting("Rule waf", 0, "Delete rule failed")
                return status_code_500("delete.rule.fail.server")
            finally:
                self.session.close()
                self.engine_connect.dispose()
            return status_code_200("delete.rule.success", {})
        except Exception as e:
            monitor_setting = log_setting("Rule waf", 0, "Delet rule failed")
            self.logger.log_writer.error(f"Delete rule faile client, {e}")
            return status_code_400("delete.rule.fail.client")
        finally:
            self.session.close()
            self.engine_connect.dispose()


    def read_rule_detail(self, rule_id, waf_rule_id):
        rule_waf_detail = self.session.query(RuleOtherBase, RuleOtherDetailBase).outerjoin(RuleOtherBase). \
            filter(RuleOtherBase.id.__eq__(waf_rule_id)). \
            filter(RuleOtherDetailBase.id.__eq__(rule_id)).first()

        if rule_waf_detail:
            rule_waf_base = {
                "id": rule_waf_detail.RuleOtherDetailBase.id,
                "id_rule": rule_waf_detail.RuleOtherDetailBase.id_rule,
                "rule_name": rule_waf_detail.RuleOtherBase.name,
                "rules": rule_waf_detail.RuleOtherDetailBase.rules,
                "description": rule_waf_detail.RuleOtherDetailBase.description,
                "message":rule_waf_detail.RuleOtherDetailBase.message,
                "tag":rule_waf_detail.RuleOtherDetailBase.tag.split(","),
                "path_rule":rule_waf_detail.RuleOtherDetailBase.path_rule
            }
            return rule_waf_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def write_file(self, waf_rule_id):
        data = []
        list_rule_detail = self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.waf_rule_id.__eq__(waf_rule_id)).all()
        for rule_waf in list_rule_detail:
            data.append(self.read_rule_detail(rule_waf.id, waf_rule_id))
        self.session.close()  
        self.engine_connect.dispose()       
        pathArray = {}
        for rule in data:
            if rule['path_rule'] not in pathArray:
                pathArray[rule['path_rule']] = [rule]
            else:
                pathArray[rule['path_rule']].append(rule)
        
        for path in pathArray:
            f = open(path, "w")
            f.write("\n".join(rule['rules'] for rule in pathArray[path]))
            f.close()  
   
  
