from sqlalchemy import or_

from app.functions.objects.website.website_core import Website
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.web_server import ngx_config_remove_backup, ngx_add_website_to_group_website, \
    ngx_remove_website_from_group_website, ngx_config_rollback, ngx_group_website_init_config, ngx_config_backup, \
    ngx_remove_group_website_config, ngx_reload
from app.libraries.data_format.id_helper import get_default_value
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import GroupWebsiteBase
from app.model import WebsiteBase, CRSBase, TrustwaveBase, RuleOtherDetailBase, AntiVirusBase
from app.model import GroupWebsiteHaveCRS, GroupWebsiteHaveTrustwave, GroupWebsiteHaveRuleOther, AntiVirusHaveGroupWebsite


def verify_json_data(json_data):
    
    verify = ""
    if "name" in json_data and len(json_data["name"]) > 100:
            verify += "name too long, "
                
    if "description" in json_data and len(json_data["description"]) > 500:
        verify += "description too long, "

    if "action" in json_data:
        if json_data['action'] not in ["add", "remove"]:
            verify += f"action {json_data['action']} not true, "
        if 'website_id' in json_data:
            if not str(json_data['website_id']).isdigit():
                verify += f"website_id {json_data['website_id']} is not digit, "
        else:
            verify += f"website_id missing, "

    return verify


class GroupWebsite(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("group_website")

    def get_all_group_website(self, http_parameters):
        limit, offset, order = get_default_value(self.logger.log_writer, http_parameters, GroupWebsiteBase)
        list_group_website_id = self.session.query(GroupWebsiteBase.id).outerjoin(WebsiteBase)
        # optional parameter
        if "search" in http_parameters:
            search_string = http_parameters["search"]
            base_column = list(GroupWebsiteBase.__table__.columns)
            website_column = list(WebsiteBase.__table__.columns)
            list_column = base_column + website_column
            list_group_website_id = list_group_website_id.filter(
                or_(key.like(f"%{search_string}%") for key in list_column)
            )
        # group result
        list_group_website_id = list_group_website_id.group_by(GroupWebsiteBase.id).order_by(order)
        # get final result
        number_of_group_website = list_group_website_id.count()
        list_group_website_id = list_group_website_id.limit(limit).offset(offset).all()
        # read result
        all_group_website_base_data = []
        for group_id in list_group_website_id:
            all_group_website_base_data.append(self.read_group_website_detail(group_id.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_group_website_base_data, number_of_group_website, limit, offset)
        )

    def add_new_group_website(self, group_website_json_data):
        json_error = verify_json_data(group_website_json_data)
        if json_error:
            self.logger.log_writer.error(f"Json data error, {json_error}")
            return status_code_400("post.group.website.fail.client")
        if self.session.query(GroupWebsiteBase).filter(GroupWebsiteBase.name.__eq__(group_website_json_data["name"])).first():
            self.logger.log_writer.error(f"name bi trung,")
            return status_code_400("post.group.website.fail.client")
        ngx_config_backup()
        group_website_obj = GroupWebsiteBase(
            name=group_website_json_data["name"],
            description=group_website_json_data["description"],
            group_website_status=0
        )
        self.session.add(group_website_obj)
        self.session.flush()

        list_group_rule_crs = self.session.query(CRSBase.id).all()
        for group_rule_crs in list_group_rule_crs:
            rule_crs = GroupWebsiteHaveCRS(group_website_id=group_website_obj.id, crs_id=group_rule_crs.id, group_rule_status=1)
            self.session.add(rule_crs)
        self.session.flush()

        list_group_rule_trust = self.session.query(TrustwaveBase.id).all()
        for group_rule_trust in list_group_rule_trust:
            rule_trust = GroupWebsiteHaveTrustwave(group_website_id=group_website_obj.id, trustwave_id=group_rule_trust.id, group_rule_status=1)
            self.session.add(rule_trust)
        self.session.flush()

        list_group_rule_other = self.session.query(RuleOtherDetailBase.id).all()
        for group_rule_other in list_group_rule_other:
            rule_other = GroupWebsiteHaveRuleOther(group_website_id=group_website_obj.id, rule_other_id=group_rule_other.id, group_rule_status=1)
            self.session.add(rule_other)
        self.session.flush()
        
        list_group_anti_virus = self.session.query(AntiVirusBase.id).all()
        for group_anti_virus in list_group_anti_virus:
            anti_virus = AntiVirusHaveGroupWebsite(group_website_id=group_website_obj.id, anti_id=group_anti_virus.id, group_rule_status=1)
            self.session.add(anti_virus)
        self.session.flush()
        # core
        config_success = ngx_group_website_init_config(group_website_obj.id)
        # db
        if config_success:
            try:
                self.session.commit()
                ngx_config_remove_backup()
                ngx_reload()
                monitor_setting = log_setting("Group website", 1, "Add new Group website")
                return status_code_200("post.group.website.success",
                                       self.read_group_website_detail(group_website_obj.id))
            except Exception as e:
                self.logger.log_writer.error(f"Add group website fail, {e}")
                monitor_setting = log_setting("Group website", 0, "Add new Group website failed")
                self.session.rollback()
            finally:
                self.session.close()
                self.engine_connect.dispose()
        ngx_config_rollback()
        return status_code_500("post.group.website.fail.server")

    def get_group_website_detail(self, group_website_id):
        group_website_detail = self.read_group_website_detail(group_website_id)
        if bool(group_website_detail):
            return get_status_code_200(group_website_detail)
        else:
            return status_code_400("get.group.website.fail.client")

    def edit_group_website(self, group_website_id, group_website_json_data):
        # chi sua thong tin ve group website tuong tac voi db nen khong can backup
        json_error = verify_json_data(group_website_json_data)
        if json_error:
            self.logger.log_writer.error(f"Json data error, {json_error}")
            return status_code_400("put.group.website.fail.client")
        if self.session.query(GroupWebsiteBase).filter(GroupWebsiteBase.name.__eq__(group_website_json_data["name"])).\
            filter(GroupWebsiteBase.id.__ne__(group_website_id)).first():
            self.logger.log_writer.error(f"name bi trung,")
            return status_code_400("put.group.website.fail.client")
        group_website_detail = self.read_group_website_detail(group_website_id)
        group_website_detail.update(group_website_json_data)
        group_website_obj = self.session.query(GroupWebsiteBase). \
            filter(GroupWebsiteBase.id.__eq__(group_website_id)).one()
        group_website_obj.name = group_website_detail["name"]
        group_website_obj.description = group_website_detail["description"]
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting("Group website", 1, "Edit Group website")
        except Exception as e:
            self.logger.log_writer.error(f"Edit group website fail, {e}")
            monitor_setting = log_setting("Group website", 0, "Edit Group website")
            return status_code_500("put.group.website.fail.server")
        finally:
            group_detail = self.read_group_website_detail(group_website_id)
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("put.group.website.success", group_detail)

    def delete_group_website(self, group_website_id):
        group_website_detail = self.read_group_website_detail(group_website_id)
        if bool(group_website_detail):
            ngx_config_backup()
            # core
            for website in group_website_detail["websites"]:
                ngx_remove_website_from_group_website(website["website_domain"], check_config=False)
                website_obj = self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website["id"])).first()
                website_obj.group_website_id = None
                self.session.flush()
            config_success = ngx_remove_group_website_config(group_website_id)
            self.session.query(GroupWebsiteBase).filter(GroupWebsiteBase.id.__eq__(group_website_id)).delete()
            if config_success:
                self.session.flush()
                # db
                try:
                    self.session.commit()
                    ngx_config_remove_backup()
                    monitor_setting = log_setting("Group website", 1, "Delete Group website")
                    return status_code_200("delete.website.to.group.website.success", {})
                except Exception as e:
                    self.logger.log_writer.error(f"Delete group website fail, {e}")
                    monitor_setting = log_setting("Group website", 0, "Delete Group website failed")
                finally:
                    self.session.close()
                    self.engine_connect.dispose()
            ngx_config_rollback()
            return status_code_500("delete.group.website.fail.server")
        else:
            return status_code_400("delete.group.website.fail.client")

    def add_or_remove_website_to_group(self, group_website_id, group_website_json_data):
        error_code = verify_json_data(group_website_json_data)
        if error_code != "":
            self.logger.log_writer.error(f"Data not validate {error_code}")
            return status_code_400("post.website.to.group.website.fail.client")
        website_id = group_website_json_data["website_id"]
        web = Website()
        website_detail = web.read_website_detail(website_id)
        if bool(website_detail):
            ngx_config_backup()
            # add website to group
            website_obj = self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website_id)).first()
            # core
            if group_website_json_data["action"] == "add":
                config_success = ngx_add_website_to_group_website(website_obj.website_domain, group_website_id)
                website_obj.group_website_id = group_website_id
            else:
                config_success = ngx_remove_website_from_group_website(website_obj.website_domain)
                website_obj.group_website_id = None
            self.session.flush()
            if config_success:
                # db
                try:
                    self.session.commit()
                    ngx_config_remove_backup()
                    ngx_reload()
                    monitor_setting = log_setting("Group website", 1, "Update website in Group website")
                    return status_code_200("post.website.to.group.website.success", group_website_json_data)
                except Exception as e:
                    self.logger.log_writer.error(f"Add website to group website fail, {e}")
                    monitor_setting = log_setting("Group website", 0, "Update website in Group website failed")
                finally:
                    self.session.close()
                    self.engine_connect.dispose()
            ngx_config_rollback()
            monitor_setting = log_setting("Group website", 0, "Update website in Group website failed")
            return status_code_500("post.website.to.group.website.fail.server")
        else:
            monitor_setting = log_setting("Group website", 0, "Update website in Group website failed")
            return status_code_400("post.website.to.group.website.fail.client")

    def read_group_website_detail(self, group_website_id):
        group_website_detail = self.session.query(GroupWebsiteBase). \
            filter(GroupWebsiteBase.id.__eq__(group_website_id)).one()
        if group_website_detail:
            group_website_base_data = {
                "id": group_website_detail.id,
                "name": group_website_detail.name,
                "description": group_website_detail.description,
                "websites": []
            }
            list_website_id = self.session.query(WebsiteBase.id). \
                filter(WebsiteBase.group_website_id.__eq__(group_website_id)).all()
            for website_id in list_website_id:
                web = Website()
                website_detail = web.read_website_detail(website_id.id)
                group_website_base_data["websites"].append(website_detail)
            self.session.close()
            self.engine_connect.dispose()
            return group_website_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
