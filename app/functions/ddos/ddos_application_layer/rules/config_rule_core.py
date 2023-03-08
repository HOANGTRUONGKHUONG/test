from app.functions.ddos.ddos_application_layer.URI.ddos_application_layer_uri_core import DDosApplicationUri
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.web_server import *
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import *
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting


class ConFigRule(object):
    def __init__(self):
        self.logger = c_logger("ddos_application")
        self.uri = DDosApplicationUri()

    def get_all_rules(self, http_parameters):
        if "group_websites" in http_parameters:
            http_parameters["group_website_id"] = http_parameters["group_websites"]
        self.session, self.engine_connect = ORMSession_alter()
        list_rules, number_of_rule = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                         DDosApplicationBase)
        all_rule_base_data = []
        for rule in list_rules:
            all_rule_base_data.append(self.read_rule_detail(rule.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_rule_base_data, number_of_rule, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def add_new_rule(self, json_data):
        # Add data to  ddos_application_layer table
        self.session, self.engine_connect = ORMSession_alter()
        rule_obj = DDosApplicationBase(name=json_data["name"], count=json_data["count"],
                                       time=json_data["time"], active=json_data["active"],
                                       group_website_id=json_data["group_website_id"],
                                       block_time=json_data["block_time"],
                                       status=json_data["status"],
                                       rule_type=json_data["rule_type"])
        self.session.add(rule_obj)
        self.session.flush()
        try:
            self.session.commit()
        except Exception as e:
            self.logger.log_writer.error(f"add rule fail, {e}")
            monitor_setting = log_setting("Application rule", 0, "Add new rule failed")
            return status_code_500("post.rule.fail.server")
        for i in set(json_data["urls"]):
            # Add data to ddos_application_layer_uri table
            try:
                uri_id = self.session.query(URIBase.id).filter(URIBase.uri.__eq__(i)).first()
                # Add data to ddos_application_has_uri table
                rule_url_obj = DDosApplicationUriBase(uri_id=uri_id.id, ddos_app_id=rule_obj.id)
            except Exception:
                uri_obj = URIBase(uri=i)
                self.session.add(uri_obj)
                self.session.flush()
                try:
                    self.session.commit()
                except Exception as e:
                    self.logger.log_writer.error(f"add rule fail, {e}")
                    monitor_setting = log_setting("Application rule", 0, "Add new rule failed")
                    return status_code_500("post.rule.fail.client")
            # Add data to ddos_application_has_uri table
            uri_id = self.session.query(URIBase.id).filter(URIBase.uri.__eq__(i)).first()
            rule_url_obj = DDosApplicationUriBase(uri_id=uri_id.id, ddos_app_id=rule_obj.id)
            self.session.add(rule_url_obj)
        # Add data to ddos_application_has_website table
        for i in json_data["website_id"]:
            rule_website_obj = DdosApplicationWebsiteBase(website_id=i, ddos_app_id=rule_obj.id)
            self.session.add(rule_website_obj)
        self.session.flush()
        try:
            self.session.commit()
        except Exception as e:
            # raise e
            self.logger.log_writer.error(f"post.rule.fail, {e}")
            monitor_setting = log_setting("Application rule", 0, "Add new rule failed")
            return status_code_500("post.rule.fail.server")
        ngx_config_backup()
        website = self.export_domain_name()
        for i in website["none_ddos"]:
            dump_ips_empty_config(i)
        for i in website["ddos"]:
            dump_ips_config(generate_ips_config_data(self.session, i))
        if ngx_check_config():
            ngx_config_remove_backup()
            ngx_reload()
        else:
            self.logger.log_writer.error("config file error")
            ngx_config_rollback()

        
        data = self.read_rule_detail(rule_obj.id)
        
        monitor_setting = log_setting("Application rule", 1, "Add new rule")
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("post.rule.success", data)

    def get_rule_detail(self, rule_id):
        rule_detail = self.read_rule_detail(rule_id)
        if bool(rule_detail):
            return get_status_code_200(rule_detail)
        else:
            return status_code_400("post.rule.fail.client")

    def edit_a_rule(self, rule_id, json_data):
        self.session, self.engine_connect = ORMSession_alter()
        rule_detail = self.read_rule_detail(rule_id)
        rule_detail.update(json_data)
        rule_obj = self.session.query(DDosApplicationBase).filter(DDosApplicationBase.id.__eq__(rule_id)).one()
        rule_obj.name = rule_detail["name"]
        rule_obj.count = rule_detail["count"]
        rule_obj.time = rule_detail["time"]
        rule_obj.block_time = rule_detail["block_time"]
        rule_obj.rule_type = rule_detail["rule_type"]
        rule_obj.active = rule_detail["active"]
        rule_obj.status = rule_detail["status"]
        rule_obj.group_website_id = rule_detail["group_website_id"]
        self.session.query(DDosApplicationUriBase). \
            filter(DDosApplicationUriBase.ddos_app_id.__eq__(rule_id)).delete()
        self.session.query(DdosApplicationWebsiteBase). \
            filter(DdosApplicationWebsiteBase.ddos_app_id.__eq__(rule_id)).delete()
        self.session.flush()
        for i in set(json_data["urls"]):
            # Add data to ddos_application_layer_uri table
            try:
                uri_id = self.session.query(URIBase.id).filter(URIBase.uri.__eq__(i)).first()
                # Add data to ddos_application_has_uri table
                rule_url_obj = DDosApplicationUriBase(uri_id=uri_id.id, ddos_app_id=rule_obj.id)
            except Exception:
                uri_obj = URIBase(uri=i)
                self.session.add(uri_obj)
                self.session.flush()
                try:
                    self.session.commit()
                except Exception as e:
                    self.logger.log_writer.error(f"put.rule.fail, {e}")
                    monitor_setting = log_setting("Application rule", 0, "Edit rule failed")
                    return status_code_500("put.rule.fail.server")
            # Add data to ddos_application_has_uri table
            uri_id = self.session.query(URIBase.id).filter(URIBase.uri.__eq__(i)).first()
            rule_url_obj = DDosApplicationUriBase(uri_id=uri_id.id, ddos_app_id=rule_obj.id)
            self.session.add(rule_url_obj)
        for i in json_data["website_id"]:
            rule_website_obj = DdosApplicationWebsiteBase(website_id=i, ddos_app_id=rule_obj.id)
            self.session.add(rule_website_obj)
        self.session.flush()
        try:
            self.session.commit()
        except Exception as e:
            self.logger.log_writer.error(f"put.rule.fail, {e}")
            monitor_setting = log_setting("Application rule", 0, "Edit rule failed")
            return status_code_500("put.rule.fail.server")
        ngx_config_backup()
        website = self.export_domain_name()
        for i in website["none_ddos"]:
            dump_ips_empty_config(i)
        for i in website["ddos"]:
            dump_ips_config(generate_ips_config_data(self.session, i))
        if ngx_check_config():
            ngx_config_remove_backup()
            ngx_reload()
        else:
            self.logger.log_writer.error("config file error")
            ngx_config_rollback()
        data = self.read_rule_detail(rule_id)
        monitor_setting = log_setting("Application rule", 1, "Edit rule")
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("put.rule.success", data)

    def delete_rule(self, rule_id):
        self.session, self.engine_connect = ORMSession_alter()
        self.session.query(DDosApplicationUriBase). \
            filter(DDosApplicationUriBase.ddos_app_id.__eq__(rule_id)).delete()
        self.session.query(DdosApplicationWebsiteBase). \
            filter(DdosApplicationWebsiteBase.ddos_app_id.__eq__(rule_id)).delete()
        self.session.query(DDosApplicationBase).filter(DDosApplicationBase.id.__eq__(rule_id)).delete()
        try:
            self.session.commit()
            monitor_setting = log_setting("Application rule", 1, "Delete rule")
        except Exception as e:
            self.logger.log_writer.error(f"Delete rule fail, {e}")
            monitor_setting = log_setting("Application rule", 0, "Delete rule failed")
            return status_code_500("Delete.rule.fail.server")
        ngx_config_backup()
        website = self.export_domain_name()
        for i in website["none_ddos"]:
            dump_ips_empty_config(i)
        for i in website["ddos"]:
            dump_ips_config(generate_ips_config_data(self.session, i))
        if ngx_check_config():
            ngx_config_remove_backup()
            ngx_reload()
        else:
            self.logger.log_writer.error("config file error")
            ngx_config_rollback()
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("Delete.rule.success", {})

    def read_rule_detail(self, rule_id):
        self.session, self.engine_connect = ORMSession_alter()
        list_rule_detail = self.session.query(DDosApplicationBase).filter(
            DDosApplicationBase.id.__eq__(rule_id)).first()
        website_inform = self.session.query(DdosApplicationWebsiteBase).outerjoin(WebsiteBase). \
            filter(DdosApplicationWebsiteBase.ddos_app_id.__eq__(rule_id)).all()
        uri_inform = self.session.query(DDosApplicationUriBase, URIBase).outerjoin(URIBase). \
            filter(DDosApplicationUriBase.ddos_app_id.__eq__(rule_id)).all()
        website = []
        uri = []
        for i in uri_inform:
            uri_base = {
                "uri_id": i.URIBase.id if i.URIBase is not None else None,
                "uri": i.URIBase.uri if i.URIBase is not None else None
            }
            uri.append(uri_base)
        for i in website_inform:
            website_base = {
                "website_id": i.object_website.id if i.object_website is not None else None,
                "website": i.object_website.website_domain if i.object_website is not None else None
            }
            website.append(website_base)
        if list_rule_detail:
            rule_data_base = {
                "id": list_rule_detail.id,
                "name": list_rule_detail.name,
                "count": list_rule_detail.count,
                "rule_type": list_rule_detail.rule_type,
                "time": list_rule_detail.time,
                "active": list_rule_detail.active,
                "status": "block",
                "block_time": list_rule_detail.block_time,
                "group_websites": {
                    "group_website_id": list_rule_detail.object_group_website.id if
                    list_rule_detail.object_group_website is not None else None,
                    "group_website": list_rule_detail.object_group_website.name if
                    list_rule_detail.object_group_website is not None else None
                },
                "websites": website,
                "urls": uri
            }
            return rule_data_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def export_domain_name(self):
        self.session, self.engine_connect = ORMSession_alter()
        list_id = self.session.query(WebsiteBase).all()
        ddos_web = []
        none_ddos_web = []
        for i in list_id:
            check_domain = self.session.query(WebsiteBase, DdosApplicationWebsiteBase).outerjoin(WebsiteBase). \
                filter(DdosApplicationWebsiteBase.website_id.__eq__(i.id)).first()
            if check_domain:
                ddos_web.append(i.website_domain)
            else:
                none_ddos_web.append(i.website_domain)
        result = {
            "ddos": ddos_web,
            "none_ddos": none_ddos_web
        }
        self.session.close()
        self.engine_connect.dispose()
        return result
