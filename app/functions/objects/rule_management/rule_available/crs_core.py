from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.parseRule import parseRule
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import RuleAvailableBase, CRSBase
import msc_pyparser
from flask import send_file
#from app.setting import WAF_CONFIG_DIR
import os
import zipfile

FILEDIR = "/home/bwaf/modsec/owasp-modsecurity-crs/rules/"

def verify_input(json_data):
    verify = ""
    # check length rule_detail
    if "rule_detail" in json_data and len("json_data") > 65000:
        verify += "rule_detail too long, " 
        
    return verify

class CRSRule(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("crs_rule")

    def get_all_crs_rule(self, http_parameters, rule_available_id):
       # self.dong_bo_data(rule_available_id)
        
        list_crs_detail_id, number_of_crs_detail = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                                    CRSBase)
            
        all_crs_detail_base_data = []
        for crs in list_crs_detail_id: 
            all_crs_detail_base_data.append(self.read_crs_rule_detail(crs.id, rule_available_id))

        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(
            all_crs_detail_base_data, number_of_crs_detail, http_parameters["limit"], http_parameters["offset"]
        ))
        

    def get_crs_rule_detail(self, crs_id, rule_available_id):
        self.dong_bo_data(rule_available_id)
        crs_detail = self.read_crs_rule_detail(crs_id, rule_available_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(crs_detail):
            return status_code_200("get.rule.success", crs_detail)
        else:
            return status_code_400("get.rule.fail.client")

    def edit_crs_rule(self, json_data, crs_id, rule_available_id):
        json_error = verify_input(json_data)
        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("put.rule.fail.client")
        #rule_crs_detail = self.read_crs_rule_detail(crs_id, rule_available_id)
        # rule_crs_detail_obj = self.session.query(CRSBase).filter(CRSBase.id.__eq__(crs_id)).one()
        # rule_crs_detail_obj.rule_detail = rule_crs_detail["rule_detail"]
        mparser = msc_pyparser.MSCParser()
        try:
            mparser.parser.parse(json_data['rule_detail'])
        except Exception as exp:
            return status_code_400("put.rule.fail.client")
        parsed = mparser.configlines
        for rules in parsed:
            if rules.get("type") == "SecRule" or rule.get("type") == "SecAction":
                rule = rules["actions"]
                rule_detail = {
                    "id_rule": ""
                }
                for action in rule:
                    if action['act_name'] == "id":
                        rule_detail["id_rule"] = action['act_arg']
                
                if self.session.query(CRSBase).filter(CRSBase.id_rule.__eq__(rule_detail["id_rule"])).\
                    filter(CRSBase.id.__ne__(crs_id)).first():
                    self.logger.error(f"id rule trung, ")
                    return status_code_400("put.crs.rule.fail.client")
       
        self.session.query(CRSBase).filter(CRSBase.id == crs_id).update(json_data)
        # self.session.flush()
        try:
            self.session.commit()
            self.write_file(rule_available_id)
            self.dong_bo_data(rule_available_id)
            data = self.read_crs_rule_detail(crs_id, rule_available_id)
          #  self.dong_bo_data(rule_available_id)
            monitor_setting = log_setting("Rule crs", 1, "Edit rule ")
            
        except Exception as e:
          #  raise e
            self.logger.log_writer.error(f"Edit rule crs fail, {e}")
            monitor_setting = log_setting("Rule crs", 0, "Edit rule crs failed")
            return status_code_500("put.crs.rule.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("put.crs.rule.success", data)


    def read_crs_rule_detail(self, crs_id, rule_available_id):
        rule_detail_infor = self.session.query(RuleAvailableBase, CRSBase).outerjoin(RuleAvailableBase). \
                    filter(RuleAvailableBase.id.__eq__(rule_available_id)).filter(CRSBase.id.__eq__(crs_id)).first()
                
        if rule_detail_infor:
            infor = {
                    "id": rule_detail_infor.CRSBase.id,
                    "rule_available_name": rule_detail_infor.RuleAvailableBase.rule_available_name,
                    "id_rule" : rule_detail_infor.CRSBase.id_rule,
                    "description": rule_detail_infor.CRSBase.description,
                    "msg": rule_detail_infor.CRSBase.message,
                    "tag": rule_detail_infor.CRSBase.tag.split(","),
                    "rule_detail": rule_detail_infor.CRSBase.rule_detail,
                    "path_file":rule_detail_infor.CRSBase.path_file
                    }
        
            return infor
        else:
            self.session.close()  
            self.engine_connect.dispose() 
            return {}    

    def dong_bo_data(self, rule_available_id):
        files = os.listdir(FILEDIR)
        for file in files:
           if file.endswith(".conf") and file.strip("\n") != "REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf" and file.strip("\n") != "RESPONSE-999-EXCLUSION-RULES-AFTER-CRS.conf":
            # if file.endswith(".conf") and file.strip("\n") != "rule3.conf":
                f = open(FILEDIR + file, "r")
                path_file = f"{FILEDIR+file}"
                data = f.read()
                try:
                    mparser = msc_pyparser.MSCParser()
                    mparser.parser.parse(data)
                except Exception as exp:
                    continue
                parsed = mparser.configlines
                
                for entry in parsed:
                    if entry.get("type") == "Comment" or entry.get("type") == "SecRule" or entry.get("type") == "SecAction":
                        rule_infor = {
                                "id_rule" : " ",
                                "description": "",
                                "msg": "",
                                "tag": [],
                                "path_file":""
                            }
                        list_file_rule = []
                        # if entry.get("type") == "Comment":
                        #   #  print("222:", entry)
                        #     rule_infor["description"] = entry['argument']
                        
                        if entry.get("type") == "SecRule" or entry.get("type") == "SecAction":
                            rules = entry
                            rule = rules["actions"]
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
                            rule_detail = parseRule(path_file, rule_infor["id_rule"])
                            crs_obj = CRSBase(id_rule=rule_infor["id_rule"], description=rule_infor["description"], message=rule_infor["msg"],
                                                tag=tag_str, rule_available_id=rule_available_id, rule_detail=rule_detail, path_file=path_file)
                    
                            # Add databse
                            for object in list_file_rule:
                                if not self.session.query(CRSBase).filter(CRSBase.id_rule.__eq__(object["id_rule"])).first():
                                    self.session.add(crs_obj)
                                    self.session.flush()
                                    self.session.commit()
                                
                                else: 
                                    self.session.query(CRSBase).filter(CRSBase.id_rule.__eq__(rule_infor["id_rule"])).update({"message": rule_infor["msg"],
                                                                                                                                "tag": tag_str,
                                                                                                                                "description": rule_infor["description"],
                                                                                                                                "rule_detail": rule_detail,
                                                                                                                                "path_file": path_file})
                                    self.session.commit()

                                if object["id_rule"] == " ":
                                    self.session.query(CRSBase).filter(CRSBase.id_rule.__eq__(object["id_rule"])).delete()
                                    self.session.commit()
                            
                            for obj in list_file_rule: 
                                if obj["id_rule"] == " ":
                                    list_file_rule.remove(obj)
                                if list_file_rule != []:
                                    rule = list_file_rule
            
                                query = self.session.query(CRSBase.id_rule, CRSBase.description, CRSBase.message, CRSBase.tag, CRSBase.rule_available_id, CRSBase.path_file)
                                array_crs = []
                                for row in query:
                                    array_crs.append(row._asdict())
                                abc ={}
                                if abc == obj:
                                    False
                                else:
                                    True
                                for rule in array_crs:
                                    if rule == abc:
                                        self.session.query(CRSBase).filter(CRSBase.id_rule.__eq__(rule["id_rule"])).delete()
                                        self.session.commit()
                            self.session.close()  
                            self.engine_connect.dispose()

    def write_file(self, rule_available_id):
        data = []
        list_rule_crs_detail = self.session.query(CRSBase).all()
        for rule_crs in list_rule_crs_detail:
            data.append(self.read_crs_rule_detail(rule_crs.id, rule_available_id))
        self.session.close()  
        self.engine_connect.dispose()     
        pathArray = {}
        for rule in data:
            if rule['path_file'] not in pathArray:
                pathArray[rule['path_file']] = [rule]
            else:
                pathArray[rule['path_file']].append(rule)
        
        for path in pathArray:
            f = open(path, "w")
            f.write("\n".join(rule['rule_detail'] for rule in pathArray[path]))
            f.close()                          
                       

    def download(self):              
        with zipfile.ZipFile(f"/home/bwaf/CRS.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
            self.zipdir(FILEDIR, zipf)
            zipf.close()
                
            monitor_setting = log_setting("Download", 1, "Download crs rule file")
            return send_file(f"/home/bwaf/CRS.zip", mimetype='application/zip',
                            as_attachment=True, conditional=True)
            

    def zipdir(self, path, ziph):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".conf") and file.strip("\n") != "REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf" and \
                    file.strip("\n") != "RESPONSE-999-EXCLUSION-RULES-AFTER-CRS.conf":
                        
                    ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))