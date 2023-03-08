from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.parseRule import parseRule
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500, status_code_201
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from flask import send_file
import os
import shutil
import msc_pyparser
from app.model import RuleOtherBase, RuleOtherDetailBase
import zipfile

def verify_input(other_rule_json_data):
    verify = ""
    # check length name và check trùng tên bộ luật 
    if "name" in other_rule_json_data and len(other_rule_json_data["name"]) > 100:
            verify += "name too long, "
    # check length description
    if "description" in other_rule_json_data and len(other_rule_json_data["description"]) > 500:
        verify += "description too long, "

    if "rule_other_status" in other_rule_json_data:
        if other_rule_json_data["rule_other_status"] not in [1, 0]:
            verify += f"rule_other_status {other_rule_json_data['rule_other_status']} not validate, "

    return verify

class RuleOther(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("rule_other")

    def get_all_rule_other(self, http_parameters):
        list_rule_other_id, number_of_rule_other = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                    RuleOtherBase)

        all_rule_other_base_data = []
        for rule_other in list_rule_other_id:
            all_rule_other_base_data.append(self.read_rule_other_detail(rule_other.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(
            all_rule_other_base_data, number_of_rule_other, http_parameters["limit"], http_parameters["offset"]
        ))


    def add_new_rule_other(self, other_rule_json_data):
        json_error = verify_input(other_rule_json_data)
        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("add.new.rule.other.fail.client")
        if self.session.query(RuleOtherBase).filter(RuleOtherBase.name.__eq__(other_rule_json_data["name"])).first():
            self.logger.log_writer.error(f"name bi trung,")
            return status_code_400("add.new.rule.other.fail.client")

        other_rule_obj = RuleOtherBase(name=other_rule_json_data["name"], description=other_rule_json_data["description"], rule_other_status=0)
        self.session.add(other_rule_obj)
        self.session.flush()
        try:
            self.session.commit()
            self.create_file(other_rule_obj.id)
            monitor_setting = log_setting("Rule other", 1, "Add new rule other")
            data = self.read_rule_other_detail(other_rule_obj.id)
            return status_code_200("post.rule.other.success", data)
        except Exception as e:
            monitor_setting = log_setting("Rule other", 0, "Add new rule other failed")
            self.logger.log_writer.error(f"Add rule fail,{e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("post.rule.other.fail.server")

    def get_rule_other_detail(self, waf_rule_id):
        rule_other_detail = self.read_rule_other_detail(waf_rule_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(rule_other_detail):
            return status_code_200("get.rule.other.success", rule_other_detail)
        else:
            return status_code_400("get.rule.other.fail.client")

    def edit_rule_other(self, waf_rule_id, other_rule_json_data):
        json_error = verify_input(other_rule_json_data)
        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("put.rule.other.fail.client")
        if self.session.query(RuleOtherBase).filter(RuleOtherBase.name.__eq__(other_rule_json_data["name"])).\
            filter(RuleOtherBase.id.__ne__(waf_rule_id)).first():
            self.logger.log_writer.error(f"name bi trung,")
            return status_code_400("put.rule.other.fail.client")
        rule_other_detail = self.read_rule_other_detail(waf_rule_id)
        rule_other_detail.update(other_rule_json_data)
        other_rule_obj = self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).one()
        other_rule_obj.name = rule_other_detail["name"]
        other_rule_obj.description = rule_other_detail["description"]
        other_rule_obj.rule_other_status = rule_other_detail["rule_other_status"]
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting("Rule other", 1, "Edit rule other")
            data = self.read_rule_other_detail(waf_rule_id)
        except Exception as e:
            self.logger.log_writer.error(f"Edit rule other fail, {e}")
            monitor_setting = log_setting("Rule other", 0, "Edit rule other failed")
            return status_code_500("put.rule.other.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("put.rule.other.success", data)


    def delete_rule_other(self, waf_rule_id):
        try:
            self.delete_file(waf_rule_id)
            self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).delete()
            try:
                self.session.commit()
                monitor_setting = log_setting("Rule other", 1, "Delete rule other")
            except Exception as e:
                self.logger.log_writer.error(f"Delete rule other fail, {e}")
                monitor_setting = log_setting("Rule other", 0, "Delete rule other failed")
                return status_code_500("delete.rule.other.fail.server")
            finally:
                self.session.close()
                self.engine_connect.dispose()
            return status_code_200("delete.rule.other.success", {})
        except Exception as e:
            monitor_setting = log_setting("Rule other", 0, "Delet rule other failed")
            self.logger.log_writer.error(f"Delete rule other faile client, {e}")
            return status_code_400("delete.rule.other.fail.client")
        finally:
            self.session.close()
            self.engine_connect.dispose()



    def read_rule_other_detail(self, waf_rule_id):
        rule_other_detail = self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).first()
        if rule_other_detail:
            rule_other_base_data = {
                "id": rule_other_detail.id,
                "name": rule_other_detail.name,
                "description": rule_other_detail.description,
                "rule_other_status": rule_other_detail.rule_other_status
            }
            return rule_other_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
    
    def create_file(self, waf_rule_id):
        list_rule_other = self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).first()
        rule_id = list_rule_other.id
        self.session.close()  
        self.engine_connect.dispose()     
        if not os.path.exists(f"/home/bwaf/modsec/rule_{rule_id}"):
            os.mkdir(f"/home/bwaf/modsec/rule_{rule_id}")
        f = open(f"/home/bwaf/modsec/rule_{rule_id}/rule_{rule_id}.conf", "w")
        f.close()

    def delete_file(self, waf_rule_id):
        rule_other_delete = self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).first()
        rule_id = rule_other_delete.id
        self.session.close()  
        self.engine_connect.dispose()
        shutil.rmtree(f"/home/bwaf/modsec/rule_{rule_id}")

    def download_rule(self, waf_rule_id):
        list_file = self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).first()
        self.session.close()  
        self.engine_connect.dispose() 
        if list_file:
            rule_id = list_file.id
            with zipfile.ZipFile(f"/home/bwaf/rule_{rule_id}.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
                self.zip(f"/home/bwaf/modsec/rule_{rule_id}/", zipf)
                zipf.close()   
            monitor_setting = log_setting("Download", 1, "Download rule file")
            return send_file(f"/home/bwaf/rule_{rule_id}.zip", as_attachment=True, conditional=True)
        
    def zip(self, path, ziph):
        # ziph is zipfile handle
        for root, dirs, files in os.walk(path):
            for file in files:   
                    ziph.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(path, '..')))
            
        

    def upload_rule(self, request, waf_rule_id):
        list_file = self.session.query(RuleOtherBase).filter(RuleOtherBase.id.__eq__(waf_rule_id)).first()
        if list_file:
            rule_id = list_file.id 
            if "rule_file" in request.files:
                file = request.files["rule_file"]
                if file.filename.endswith('.zip'):
                    print("kakak: ", file.filename)
                    if not os.path.exists(f"/tmp/upload_{rule_id}"):
                        os.mkdir(f"/tmp/upload_{rule_id}")
                       
                    file.save(f"/tmp/upload_{rule_id}/{file.filename}")
                    with zipfile.ZipFile(f"/tmp/upload_{rule_id}/{file.filename}", 'r') as zip:
                        zip.extractall(f"/tmp/upload_{rule_id}/") 
                        os.remove(f"/tmp/upload_{rule_id}/{file.filename}")            
                        files = os.listdir(f"/tmp/upload_{rule_id}/")
                        for pfile in files: 
                            print("kien do 555555:", pfile)
                            if os.path.isfile(f"/tmp/upload_{rule_id}/" + pfile):
                                os.replace(f"/tmp/upload_{rule_id}/" + pfile, f"/home/bwaf/modsec/rule_{rule_id}/" + pfile)
                                f = open(f"/home/bwaf/modsec/rule_{rule_id}/{pfile}", "r")
                                path_rule = f"/home/bwaf/modsec/rule_{rule_id}/{pfile}"                   
                else:
                    file.save(f"/home/bwaf/modsec/rule_{rule_id}/{file.filename}")
                    f = open(f"/home/bwaf/modsec/rule_{rule_id}/{file.filename}", "r")
                    path_rule = f"/home/bwaf/modsec/rule_{rule_id}/{file.filename}"
                try:
                    data = f.read()
                except Exception as e:
                  #  raise e
                    os.remove(f"/home/bwaf/modsec/rule_{rule_id}/{file.filename}")
                    monitor_setting = log_setting("Upload rule", 0, "Upload rule failed")
                    self.logger.log_writer.error(f"Upload load rule faile client, {e}")
                    return status_code_400("upload.rule.fail.client")
                mparser = msc_pyparser.MSCParser()
                try:
                    mparser.parser.parse(data)
                except Exception as e:
                   # raise e
                    os.remove(f"/home/bwaf/modsec/rule_{rule_id}/{file.filename}")
                    monitor_setting = log_setting("Upload rule", 0, "Upload rule failed")
                    self.logger.log_writer.error(f"Upload load rule faile client, {e}")
                    return status_code_400("upload.rule.fail.client")
                parsed = mparser.configlines
                for rules in parsed:
                    if rules.get("type") == "SecRule" or rules.get("type") == "SecAction":
                        list_file_rule = []
                        rule = rules["actions"]
                        rule_infor = {
                                    "id_rule" : "",
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
                        rule_detail = parseRule(path_rule, rule_infor["id_rule"])
                        rule_obj = RuleOtherDetailBase(id_rule=rule_infor["id_rule"], rules=rule_detail, message=rule_infor["msg"], tag=tag_str,
                                                    waf_rule_id=waf_rule_id, path_rule=path_rule)
                
                        # Add databse
                        
                        for object in list_file_rule:
                            if object["id_rule"] == "":
                                continue
                            if not self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.id_rule.__eq__(object["id_rule"])).first():
                                self.session.add(rule_obj)
                                self.session.flush()
                                self.session.commit()
                            else:
                                print (self.session.query(RuleOtherDetailBase).filter(RuleOtherDetailBase.id_rule.__eq__(object["id_rule"])).first().__dict__)
                                os.remove(f"/home/bwaf/modsec/rule_{rule_id}/{file.filename}")
                                self.logger.log_writer.error(f"file bi trung,")
                                return status_code_400("upload.rule.fail.client")
    
                self.session.close()  
                self.engine_connect.dispose() 
                log = log_setting("upload rule", 1, "Upload a rule to server")
                return status_code_201("Upload.rule.success")

   