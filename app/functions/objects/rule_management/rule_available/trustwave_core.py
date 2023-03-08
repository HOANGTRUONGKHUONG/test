from doctest import testfile
from genericpath import exists
from re import A
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.parseRule import parseRule
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
import msc_pyparser
from flask import send_file
from app.model import RuleAvailableBase, TrustwaveBase

FILEDIR = "/home/bwaf/modsec/Trustwave_new.conf"

# FILEDIR = "/home/bwaf/test/rule3.conf"

def verify_input(json_data):
    verify = ""
    # check length rule_detail
    if "rule_detail" in json_data and len("json_data") > 65000:
        verify += "rule_detail too long, " 

    return verify

class TrustwaveRule(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("trustwave_rule")

    def get_all_trustwave_rule(self, http_parameters, rule_available_id):
      #  self.dong_bo_data(rule_available_id)

        list_trustwave_detail_id, number_of_trustwave_detail = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                                    TrustwaveBase)
            
        all_trustwave_detail_base_data = []
        for trustwave in list_trustwave_detail_id:
           
            all_trustwave_detail_base_data.append(self.read_trustwave_rule_detail(trustwave.id, rule_available_id))
                     
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(
            all_trustwave_detail_base_data, number_of_trustwave_detail, http_parameters["limit"], http_parameters["offset"]
        ))
        
        
    def get_trustwave_rule_detail(self, trustwave_id, rule_available_id):
        self.dong_bo_data(rule_available_id)
        trustwave_detail = self.read_trustwave_rule_detail(trustwave_id, rule_available_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(trustwave_detail):
            return status_code_200("get.trustwave.rule.detail.success", trustwave_detail)
        else:
            return status_code_400("get.trustwave.rule.fail.client")

    def edit_trustwave_rule(self, json_data, trustwave_id, rule_available_id):
        json_error = verify_input(json_data)
        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("put.rule.fail.client")
        # rule_trustwave_detail = self.read_trustwave_rule_detail(trustwave_id, rule_available_id)
        # rule_trustwave_detail.update(json_data)
        # rule_trustwave_detail_obj = self.session.query(TrustwaveBase).filter(TrustwaveBase.id.__eq__(trustwave_id)).one()
        # rule_trustwave_detail_obj.rule_detail = rule_trustwave_detail["rule_detail"]
        mparser = msc_pyparser.MSCParser()
        try:
            mparser.parser.parse(json_data["rule_detail"])
        except Exception as e:
            return status_code_400("put.rule.fail.client")
        parsed = mparser.configlines
        for rules in parsed:
            if rules.get("type") == "SecRule":
                rule = rules["actions"]
                rule_detail = {
                    "id_rule": ""
                }
                for action in rule:
                    if action['act_name'] == "id":
                        rule_detail["id_rule"] = action['act_arg']
                
                if self.session.query(TrustwaveBase).filter(TrustwaveBase.id_rule.__eq__(rule_detail["id_rule"])).\
                    filter(TrustwaveBase.id.__ne__(trustwave_id)).first():
                    self.logger.error(f"id rule trung, ")
                    return status_code_400("put.trustwave.rule.fail.client")
        self.session.query(TrustwaveBase).filter(TrustwaveBase.id == trustwave_id).update(json_data)
        #self.session.flush()
        try:
            self.session.commit()
            self.write_file(rule_available_id)
            self.dong_bo_data(rule_available_id)
            monitor_setting = log_setting("Rule trustwave", 1, "Edit rule ")
            data = self.read_trustwave_rule_detail(trustwave_id, rule_available_id)
        except Exception as e:
            self.logger.log_writer.error(f"Edit rule trustwave fail, {e}")
            monitor_setting = log_setting("Rule trustwave", 0, "Edit rule trustwave failed")
            return status_code_500("put.trustwave.rule.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("put.trustwave.rule.success", data)

    def read_trustwave_rule_detail(self, trustwave_id, rule_available_id):
        rule_detail_infor = self.session.query(RuleAvailableBase, TrustwaveBase).outerjoin(RuleAvailableBase). \
                    filter(RuleAvailableBase.id.__eq__(rule_available_id)).filter(TrustwaveBase.id.__eq__(trustwave_id)).first()
         
        if rule_detail_infor:
            infor = {
                    "id": rule_detail_infor.TrustwaveBase.id,
                    "rule_available_name": rule_detail_infor.RuleAvailableBase.rule_available_name,
                    "id_rule" : rule_detail_infor.TrustwaveBase.id_rule,
                    "msg": rule_detail_infor.TrustwaveBase.message,
                    "tag": rule_detail_infor.TrustwaveBase.tag.split(","),
                    "rule_detail": rule_detail_infor.TrustwaveBase.rule_detail
                    }
        
            return infor
        else:
            self.session.close()  
            self.engine_connect.dispose() 
            return {}    

    def dong_bo_data(self, rule_available_id):
        # Doc rule tu file
        f = open(FILEDIR, "r")
        data = f.read()
        mparser = msc_pyparser.MSCParser()
        mparser.parser.parse(data)
        
        parsed = mparser.configlines
        
        for entry in parsed:
            if entry.get("type") == "SecRule":
                rules = entry
                list_file_rule = []
                rule = rules["actions"]
                rule_infor = {
                            "id_rule" : " ",
                            "msg": "",
                            "tag": []
                        }
                for action in rule:
                    if action['act_name'] == "id" or action['act_name'] == "msg" or action['act_name'] == "tag":
                        if action['act_name'] == "id":
                            rule_infor["id_rule"] = action['act_arg']

                        if action['act_name'] == "msg":
                            rule_infor["msg"] = action['act_arg']

                        if action['act_name'] == "tag":
                            rule_infor["tag"].append(action['act_arg'])

                list_file_rule.append(rule_infor)
                tag_str = ",".join(tag for tag in rule_infor['tag'])
                rule_detail = parseRule(FILEDIR, rule_infor["id_rule"])
                trustwave_obj = TrustwaveBase(id_rule=rule_infor["id_rule"], message=rule_infor["msg"], tag=tag_str, 
                                                rule_available_id=rule_available_id, rule_detail=rule_detail)
        
                # Add databse
                for object in list_file_rule:
                    if not self.session.query(TrustwaveBase).filter(TrustwaveBase.id_rule.__eq__(object["id_rule"])).first():
                        self.session.add(trustwave_obj)
                        self.session.flush()
                        self.session.commit()
                    
                    else:
                        ##Update database
                        self.session.query(TrustwaveBase).filter(TrustwaveBase.id_rule.__eq__(rule_infor["id_rule"])).update({"message": rule_infor["msg"],
                                                                                                                            "tag": tag_str,
                                                                                                                            "rule_detail": rule_detail})
                        self.session.commit()

                    if object["id_rule"] == " ":
                        self.session.query(TrustwaveBase).filter(TrustwaveBase.id_rule.__eq__(object["id_rule"])).delete()
                        self.session.commit()

                for obj in list_file_rule: 
                    if obj["id_rule"] == " ":
                        list_file_rule.remove(obj)
                    if list_file_rule != []:
                        list_rule = list_file_rule
        
                        query = self.session.query(TrustwaveBase.id_rule, TrustwaveBase.message, TrustwaveBase.tag, TrustwaveBase.rule_available_id)
                        array_trustwave = []
                        for row in query:
                            array_trustwave.append(row._asdict())
                        abc ={}
                        if abc == obj:
                            False
                        else:
                            True
                        for rule in array_trustwave:
                            if rule == abc:
                                self.session.query(TrustwaveBase).filter(TrustwaveBase.id_rule.__eq__(rule["id_rule"])).delete()
                                self.session.commit()
       
                self.session.close()  
                self.engine_connect.dispose() 


    def write_file(self, rule_available_id):
        data = []
        list_rule_trust_detail = self.session.query(TrustwaveBase).all()
        for rule_trust in list_rule_trust_detail:
            data.append(self.read_trustwave_rule_detail(rule_trust.id, rule_available_id))
        self.session.close()
        self.engine_connect.dispose()       
        rules = ""
        for i in range(0, len(data)):
            rules = rules + f'{data[i]["rule_detail"]}\n'

        f = open(f"{FILEDIR}", "w")
        f.write(rules)
        f.close()

    def download(self):
        return send_file(f"{FILEDIR}", as_attachment=True, conditional=True)