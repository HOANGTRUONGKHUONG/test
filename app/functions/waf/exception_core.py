from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table, get_default_value
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import ExceptionBase, WebsiteBase
from app.libraries.configuration.web_config import from_database_to_file
import msc_pyparser

def verify_input(json_data):
    verify = ""
    # check length description
    if "description" in json_data and len(json_data["description"]) > 500:
        verify += "description too long, "
    
    # if "rules" in json_data:
    #     mparser = msc_pyparser.MSCParser()
    #     try:
    #         mparser.parser.parse(json_data["rules"])
    #     except Exception as e:
    #         verify += "rules failed, "

    return verify


class ExceptionConfig(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("exception")

    def get_all_exception(self, http_parameters, website_id):
        limit, offset, order = get_default_value(self.logger.log_writer, http_parameters, ExceptionBase)
        list_exception_detail_id = self.session.query(ExceptionBase.id).filter(ExceptionBase.website_id.__eq__(website_id))
        list_exception_detail_id = list_exception_detail_id.group_by(ExceptionBase.id).order_by(order)
        
        number_of_exception_detail = list_exception_detail_id.count()
        list_exception_detail_id = list_exception_detail_id.limit(limit).offset(offset).all()

        all_exception_detail_base_data = []
        all_exception_detail_data = []
        for exception in list_exception_detail_id:
            all_exception_detail_base_data.append(self.read_exception_detail(exception.id, website_id))

            all_exception_detail_data = list(filter(None, all_exception_detail_base_data))
                     
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(
            all_exception_detail_data, number_of_exception_detail, http_parameters["limit"], http_parameters["offset"]
        ))


    def add_new_exception(self, json_data, website_id):
        json_error = verify_input(json_data)
        if json_error:
            print("na:",json_error)
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("add.new.exception.fail.client")
        mparser = msc_pyparser.MSCParser()
        try:
            mparser.parser.parse(json_data["rules"])
        except Exception as e:
            self.logger.log_writer.error(f"rule faild, {e}")
            return status_code_400("add.new.exception.fail.client")
        parsed = mparser.configlines
        for rules in parsed:
            if rules.get("type") == "SecRule" or rule.get("type") == "SecAction":
                rule = rules["actions"]
                list_file_rule = []
                rule_infor = {
                    "id_rule": ""
                }
                for action in rule:
                    if action['act_name'] == "id":
                        rule_infor["id_rule"] = action['act_arg']
    
                if self.session.query(ExceptionBase).filter(ExceptionBase.id_rule.__eq__(rule_infor["id_rule"])).first():
                    self.logger.log_writer.error(f"id rule trung, ")
                    return status_code_400("add.new.exception.fail.client")
                exception_obj = ExceptionBase(id_rule=rule_infor["id_rule"], rules=json_data["rules"],
                    description=json_data["description"], excep_status=json_data["excep_status"], 
                    website_id=website_id)

                self.session.add(exception_obj)
                self.session.flush()
                try:
                    self.session.commit()
                    self.write_file(website_id)

                    from_database_to_file()
                
                    data = self.read_exception_detail(exception_obj.id, website_id)
                    monitor_setting = log_setting("Rule exception ", 1, "Add new exception")
                except Exception as e:
                    monitor_setting = log_setting("Rule exception", 0, "Add new exception failed")
                    self.logger.log_writer.error(f"Add exception fail,{e}")
                    return status_code_500("post.exception.fail.server")
                finally:
                    self.session.close()
                    self.engine_connect.dispose()
                return status_code_200("post.exception.success", data)

    def get_exception_detail(self, excep_id, website_id):
        exception_detail = self.read_exception_detail(excep_id, website_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(exception_detail):
            return status_code_200("get.exception.success", exception_detail)
        else:
            return status_code_400("get.exception.fail.client")

    def edit_exception(self, json_data, excep_id, website_id):
        json_error = verify_input(json_data)
        if json_error:
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("put.exception.fail.client")
        mparser = msc_pyparser.MSCParser()
        try:
            mparser.parser.parse(json_data["rules"])
        except Exception as e:
            self.logger.log_writer.error(f"rule faild, {e}")
            return status_code_400("put.exception.fail.client")
        parsed = mparser.configlines
        for rules in parsed:
            if rules.get("type") == "SecRule" or rule.get("type") == "SecAction":
                rule = rules["actions"]
                list_file_rule = []
                rule_detail = {
                    "id_rule": ""
                }
                for action in rule:
                    if action['act_name'] == "id":
                        rule_detail["id_rule"] = action['act_arg']
                  
                if self.session.query(ExceptionBase).filter(ExceptionBase.id_rule.__eq__(rule_detail["id_rule"])).\
                    filter(ExceptionBase.id.__ne__(excep_id)).first():

                    self.logger.log_writer.error(f"id rule trung, ")
                    return status_code_400("put.exception.fail.client")
        exception_detail = self.read_exception_detail(excep_id, website_id)
        exception_detail.update(json_data)
        exception_detail_obj = self.session.query(ExceptionBase).filter(ExceptionBase.id.__eq__(excep_id)).one()
        exception_detail_obj.id_rule = exception_detail["id_rule"]
        exception_detail_obj.rules = exception_detail["rules"]
        exception_detail_obj.description = exception_detail["description"]
        exception_detail_obj.excep_status = exception_detail["excep_status"]
        self.session.flush()
        try:
            self.session.commit()
            self.write_file(website_id)
            from_database_to_file()
            monitor_setting = log_setting("Rule exception", 1, "Edit rule exception")
            data = self.read_exception_detail(excep_id, website_id)
        except Exception as e:
            self.logger.log_writer.error(f"Edit exception fail, {e}")
            monitor_setting = log_setting("Rule exception", 0, "Edit rule exception failed")
            return status_code_500("put.exception.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("put.exception.success", data)

    def delete_exception(self, excep_id, website_id):
        try:
            self.session.query(ExceptionBase).filter(ExceptionBase.website_id.__eq__(website_id)). \
                filter(ExceptionBase.id.__eq__(excep_id)).delete()
            try:
                self.session.commit()
                self.write_file(website_id)
                monitor_setting = log_setting("Rule exception", 1, "Delete rule exception")
            except Exception as e:
                self.logger.log_writer.error(f"Delete exception fail, {e}")
                monitor_setting = log_setting("Rule exception", 0, "Delete exception failed")
                return status_code_500("delete.exception.fail.server")
            finally:
                self.session.close()
                self.engine_connect.dispose()
            return status_code_200("delete.exception.success", {})
        except Exception as e:
            monitor_setting = log_setting("Rule exception", 0, "Delet exception failed")
            self.logger.log_writer.error(f"Delete exception faile client, {e}")
            return status_code_400("delete.exception.fail.client")
        finally:
            self.session.close()
            self.engine_connect.dispose()



    def read_exception_detail(self, excep_id, website_id):
        rule_exception_detail = self.session.query(WebsiteBase, ExceptionBase).outerjoin(WebsiteBase). \
            filter(WebsiteBase.id.__eq__(website_id)). \
            filter(ExceptionBase.id.__eq__(excep_id)).first()

        if rule_exception_detail:
            exception_base = {
                "id": rule_exception_detail.ExceptionBase.id,
                "id_rule": rule_exception_detail.ExceptionBase.id_rule,
                "website_id": rule_exception_detail.WebsiteBase.id,
                "website_name": rule_exception_detail.WebsiteBase.website_domain,
                "rules": rule_exception_detail.ExceptionBase.rules,
                "description": rule_exception_detail.ExceptionBase.description,
                "excep_status": rule_exception_detail.ExceptionBase.excep_status
            }
            return exception_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def write_file(self, website_id):
        data = []
        list_exception_detail = self.session.query(ExceptionBase).filter(ExceptionBase.website_id.__eq__(website_id)).all()
        for rule_exception in list_exception_detail:
            data.append(self.read_exception_detail(rule_exception.id, website_id))
        self.session.close()
        self.engine_connect.dispose()
      
        rules = " "
        for i in range(0, len(data)):
            rules = rules + f'{data[i]["rules"]}\n'
            website_id = data[i]["website_id"]

        f = open(f"/home/bwaf/modsec/exception/website_{website_id}.conf", "w")
        f.write(rules)
        f.close()
