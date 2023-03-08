from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.web_config import from_database_to_file
from app.libraries.configuration.web_server import modsecurity_group_website_change_waf_status, \
    modsecurity_group_website_rules_change, ngx_reload
from app.libraries.data_format.id_helper import get_id_single_table, get_default_value, advanced_filter
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import GroupWebsiteBase, WebsiteBase
from app.model import GroupWebsiteHaveCRS, GroupWebsiteHaveTrustwave, GroupWebsiteHaveRuleOther , AntiVirusHaveGroupWebsite
from app.model import CRSBase, TrustwaveBase, RuleOtherDetailBase, AntiVirusBase, RuleOtherBase, RuleAvailableBase
from app.model import WebsiteHaveCRS, WebsiteHaveTrustwave, WebsiteHaveRuleOther , AntiVirusHaveWebsite
from sqlalchemy import or_


def verify_json_data(json_data):
    verify = ""
    if "group_rule_status" in json_data:
        if json_data["group_rule_status"] not in [1, 0]:
            verify += f"group_rule_status {json_data['group_rule_status']} not validate, "

    if "group_website_status" in json_data:
        if json_data["group_website_status"] not in [1, 0]:
            verify += f"group_website_status {json_data['group_website_status']} not validate, "

    return verify


class WAFConfiguration(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("waf_config").log_writer

    def get_all_waf_group(self, http_parameters):
        list_group_website, number_of_group_website = get_id_single_table(self.session, self.logger,
                                                                          http_parameters, GroupWebsiteBase)
        all_waf_base_data = []
        for group_website in list_group_website:
            waf_data = self.read_waf_detail(group_website.id)
            all_waf_base_data.append(waf_data)
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(all_waf_base_data, number_of_group_website,
                                      http_parameters["limit"], http_parameters["offset"]))


    def get_waf_group_detail(self, group_website_id):
        list_rule = self.read_waf_detail(group_website_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(list_rule):
            return status_code_200("get.rule.success", list_rule)
        else:
            return status_code_400("get.rule.fail.client")

    def change_waf_group_website_status(self, group_website_id, json_data):
        error_code = verify_json_data(json_data)
        if error_code != "":
            self.logger.error(error_code)
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.waf.status.fail.client")
        waf_group_detail = self.read_waf_detail(group_website_id)

        if not bool(waf_group_detail):
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.waf.status.fail.client")
        # config_status = modsecurity_group_website_change_waf_status(group_website_id=group_website_id,
        #                                                             waf_status=bool(int(json_data["waf_status"]))
        #                                                         )
        self.session.query(GroupWebsiteBase). \
            filter(GroupWebsiteBase.id.__eq__(group_website_id)).update({"group_website_status": json_data["group_website_status"]})
        # self.session.query(WebsiteBase).filter(WebsiteBase.group_website_id.__eq__(group_website_id)).update({"website_status": json_data["group_website_status"]})
        self.session.query(GroupWebsiteHaveCRS).filter(GroupWebsiteHaveCRS.group_website_id.__eq__(group_website_id)).update({"group_rule_status": json_data["group_website_status"]})
        self.session.query(GroupWebsiteHaveTrustwave).filter(GroupWebsiteHaveTrustwave.group_website_id.__eq__(group_website_id)).update({"group_rule_status": json_data["group_website_status"]})
        self.session.query(GroupWebsiteHaveRuleOther).filter(GroupWebsiteHaveRuleOther.group_website_id.__eq__(group_website_id)).update({"group_rule_status": json_data["group_website_status"]})
        self.session.query(AntiVirusHaveGroupWebsite).filter(AntiVirusHaveGroupWebsite.group_website_id.__eq__(group_website_id)).update({"group_rule_status": json_data["group_website_status"]})
        try:
            self.session.commit()
            config_status = from_database_to_file()
            if config_status is False:
                self.session.rollback()
            monitor_setting = log_setting(action="WAF", status=1, description="Change WAF status on group website")
            ngx_reload()
            return status_code_200("put.waf.status.success", self.read_waf_detail(group_website_id))
        except Exception as e:
            
            self.logger.error(f"Change waf status group {group_website_id} fail, {e}")
            self.session.rollback()
        finally:
            self.session.close()
            self.engine_connect.dispose()
        monitor_setting = log_setting(action="WAF", status=0, description="Change WAF status on group website failed")
        return status_code_500("put.waf.status.fail.server")

    def read_waf_detail(self, group_website_id):
        waf_status_detail = self.session.query(GroupWebsiteBase). \
            filter(GroupWebsiteBase.id.__eq__(group_website_id)).first()
        list_website = self.session.query(WebsiteBase).filter(WebsiteBase.group_website_id.__eq__(group_website_id)).all()
        group_website = []
        for i in list_website:
            web_base = {
                "website_id": i.id,
                "website_name": i.website_domain,
                "website_status": i.website_status
            }
            group_website.append(web_base)
        if waf_status_detail:
            waf_base = {
                "id": waf_status_detail.id,
                "name": waf_status_detail.name,
                "description": waf_status_detail.description,
                "group_website_status": waf_status_detail.group_website_status,
                "group_website": group_website
            }
            return waf_base
        else:
            return {}
        
    def get_all_rule_group(self, http_parameters, group_website_id):
        if "rule_name" in http_parameters:
            if http_parameters["rule_name"] == "crs":
                list_group_rule, number_of_group_rule = get_id_single_table(self.session, self.logger,
                                                                            http_parameters, CRSBase)
                
                all_waf_group_rule_base_data = []
                for group_rule in list_group_rule:
                    all_waf_group_rule_base_data.append(self.read_rule_group_crs_detail(group_rule.id, group_website_id))
                self.session.close()
                self.engine_connect.dispose()
                
            elif http_parameters["rule_name"] == "trustwave":
                list_group_rule, number_of_group_rule = get_id_single_table(self.session, self.logger,
                                                                            http_parameters, TrustwaveBase)
                
                all_waf_group_rule_base_data = []
                for group_rule in list_group_rule:
                    all_waf_group_rule_base_data.append(self.read_rule_group_trust_detail(group_rule.id, group_website_id))
                self.session.close()
                self.engine_connect.dispose()
                
            elif http_parameters["rule_name"] == "anti_virus":
                list_group_rule, number_of_group_rule = get_id_single_table(self.session, self.logger,
                                                                        http_parameters, AntiVirusBase)
                
                all_waf_group_rule_base_data = []
                for group_rule in list_group_rule:
                    all_waf_group_rule_base_data.append(self.read_group_anti_virus_detail(group_rule.id, group_website_id))
                self.session.close()
                self.engine_connect.dispose()
                
            else:
                limit, offset, order = get_default_value(self.logger, http_parameters, RuleOtherDetailBase)
                list_group_rule = self.session.query(RuleOtherDetailBase.id).outerjoin(GroupWebsiteHaveRuleOther).outerjoin(RuleOtherBase).\
                    filter(GroupWebsiteHaveRuleOther.group_website_id.__eq__(group_website_id)).\
                    filter(RuleOtherBase.name.__eq__(http_parameters["rule_name"]))

               # search 
                if "search" in http_parameters:
                    search_string = http_parameters["search"]
                    base_column = list(RuleOtherDetailBase.__table__.columns)
                    list_group_rule = list_group_rule.filter(
                        or_(key.like(f"%{search_string}%") for key in base_column)
                    )

                # filter
                list_group_rule = advanced_filter(http_parameters, self.logger, list_group_rule, RuleOtherDetailBase)
                
                # result
                list_group_rule = list_group_rule.group_by(RuleOtherDetailBase.id).order_by(order)
                
                number_of_group_rule = list_group_rule.count()
                list_group_rule = list_group_rule.limit(limit).offset(offset).all()
                all_waf_group_rule_base_data = []
                for group_rule in list_group_rule:
                    all_waf_group_rule_base_data.append(self.read_group_rule_other_detail(group_rule.id, group_website_id))
                self.session.close()
                self.engine_connect.dispose()
                
            return get_status_code_200(
                reformat_data_with_paging(all_waf_group_rule_base_data, number_of_group_rule,
                                        http_parameters["limit"], http_parameters["offset"]))
            

    def change_rule_of_group_website_status(self, http_parameters, json_data, rule_id, group_website_id):
        error_code = verify_json_data(json_data)
        if error_code != "":
            self.logger.error(error_code)
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.waf.rule.status.fail.client")

        if "rule_name" in http_parameters:
            try:
                if http_parameters["rule_name"] == "crs":
                    rule_detail = self.read_rule_group_crs_detail(rule_id, group_website_id)

                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")

                    self.session.query(GroupWebsiteHaveCRS).\
                        filter(GroupWebsiteHaveCRS.group_website_id.__eq__(group_website_id)).\
                        filter(GroupWebsiteHaveCRS.crs_id.__eq__(rule_id)).\
                        update({"group_rule_status": json_data["group_rule_status"]})
                        
                    self.session.query(WebsiteHaveCRS).filter(WebsiteHaveCRS.crs_id.__eq__(rule_id)).update({"rule_status": json_data["group_rule_status"]})
                    
                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
                  #  monitor_setting = log_setting(action="WAF", status=1, description="Change crs rule of group website status")
                    ngx_reload()
                    return status_code_200("put.crs.rule.status.success",
                                        self.read_rule_group_crs_detail(rule_id, group_website_id)
                                        )
                    
                elif http_parameters["rule_name"] == "trustwave":
                    rule_detail = self.read_rule_group_trust_detail(rule_id, group_website_id)

                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")
                    self.session.query(GroupWebsiteHaveTrustwave).\
                        filter(GroupWebsiteHaveTrustwave.group_website_id.__eq__(group_website_id)).\
                        filter(GroupWebsiteHaveTrustwave.trustwave_id.__eq__(rule_id)).\
                        update({"group_rule_status": json_data["group_rule_status"]})
                    self.session.query(WebsiteHaveTrustwave).filter(WebsiteHaveTrustwave.trust_id.__eq__(rule_id)).update({"rule_status": json_data["group_rule_status"]})
                    
                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
             #       monitor_setting = log_setting(action="WAF", status=1, description="Change trust rule of group website status")
                    ngx_reload()
                    return status_code_200("put.trust.rule.status.success",
                                        self.read_rule_group_trust_detail(rule_id, group_website_id)
                                        )
                        
                elif http_parameters["rule_name"] == "anti_virus":
                    rule_detail = self.read_group_anti_virus_detail(rule_id, group_website_id)
                 
                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")
                  
                    self.session.query(AntiVirusHaveGroupWebsite).\
                        filter(AntiVirusHaveGroupWebsite.group_website_id.__eq__(group_website_id)).\
                        filter(AntiVirusHaveGroupWebsite.anti_id.__eq__(rule_id)).\
                        update({"group_rule_status": json_data["group_rule_status"]})
                    self.session.query(AntiVirusHaveWebsite).filter(AntiVirusHaveWebsite.anti_id.__eq__(rule_id)).update({"rule_status": json_data["group_rule_status"]})
                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
                  #  monitor_setting = log_setting(action="WAF", status=1, description="Change anti virus of group website status")
                    ngx_reload()
                    return status_code_200("put.anti.virus.status.success",
                                        self.read_group_anti_virus_detail(rule_id, group_website_id)
                                        )

                elif http_parameters["rule_name"] == http_parameters["rule_name"]:
                    rule_detail = self.read_group_rule_other_detail(rule_id, group_website_id)

                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")

                    self.session.query(GroupWebsiteHaveRuleOther).\
                        filter(GroupWebsiteHaveRuleOther.group_website_id.__eq__(group_website_id)).\
                        filter(GroupWebsiteHaveRuleOther.rule_other_id.__eq__(rule_id)).\
                        update({"group_rule_status": json_data["group_rule_status"]})
                    
                    self.session.query(WebsiteHaveRuleOther).filter(WebsiteHaveRuleOther.rule_other_id.__eq__(rule_id)).update({"rule_status": json_data["group_rule_status"]})
                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
             #       monitor_setting = log_setting(action="WAF", status=1, description="Change group rule of website status")
                    ngx_reload()
                    return status_code_200("put.waf.group.rule.status.success",
                                        self.read_group_rule_other_detail(rule_id, group_website_id)
                                        )
                else: 
                    self.logger.error(f"Change waf rule status group {group_website_id} - rule {rule_id} fail, {e}")
                    self.session.rollback()
                
                    self.session.close()
                    self.engine_connect.dispose()
                #    monitor_setting = log_setting(action="WAF", status=1, description="Change group rule of website status failed")
                    return status_code_500("put.waf.group.rule.status.fail.server")
                    
            except Exception as e:
                self.logger.error(f"Change waf rule status group {group_website_id} - rule {rule_id} fail, {e}")
                self.session.rollback()
               # raise e

            finally:
                self.session.close()
                self.engine_connect.dispose()
            monitor_setting = log_setting(action="WAF", status=1, description="Change group rule of website status failed")
            return status_code_500("put.waf.group.rule.status.fail.server")         
            

    def read_rule_group_crs_detail(self, rule_id, group_website_id):
        rule_group_crs_detail = self.session.query(GroupWebsiteHaveCRS, CRSBase).outerjoin(CRSBase). \
                filter(GroupWebsiteHaveCRS.group_website_id.__eq__(group_website_id)). \
                filter(CRSBase.id.__eq__(rule_id)).first()

        if rule_group_crs_detail:
            rule_group_crs_base = {
                "id": rule_group_crs_detail.GroupWebsiteHaveCRS.crs_id,
                "id_rule": rule_group_crs_detail.CRSBase.id_rule,
                "description": rule_group_crs_detail.CRSBase.description,
                "msg": rule_group_crs_detail.CRSBase.message,
                "tag": rule_group_crs_detail.CRSBase.tag.split(","),
                "group_rule_status": rule_group_crs_detail.GroupWebsiteHaveCRS.group_rule_status
            }
            return rule_group_crs_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
        
    def read_rule_group_trust_detail(self, rule_id, group_website_id):
        rule_group_trust_detail = self.session.query(GroupWebsiteHaveTrustwave, TrustwaveBase).outerjoin(TrustwaveBase). \
                filter(GroupWebsiteHaveTrustwave.group_website_id.__eq__(group_website_id)). \
                filter(TrustwaveBase.id.__eq__(rule_id)).first()                                                                                                                                                       
        if rule_group_trust_detail:
            rule_group_trust_base = {
                "id": rule_group_trust_detail.GroupWebsiteHaveTrustwave.trustwave_id,
                "id_rule": rule_group_trust_detail.TrustwaveBase.id_rule,
                "msg": rule_group_trust_detail.TrustwaveBase.message,
                "tag": rule_group_trust_detail.TrustwaveBase.tag.split(","),
                "group_rule_status": rule_group_trust_detail.GroupWebsiteHaveTrustwave.group_rule_status,
            }
            return rule_group_trust_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
        
        
    def read_group_rule_other_detail(self, rule_id, group_website_id):
        group_rule_other_detail = self.session.query(GroupWebsiteHaveRuleOther, RuleOtherDetailBase).outerjoin(RuleOtherDetailBase). \
                filter(GroupWebsiteHaveRuleOther.group_website_id.__eq__(group_website_id)). \
                filter(RuleOtherDetailBase.id.__eq__(rule_id)).first()
                                                                                                                                                                                                                                                                                                                                                                                                                                
        if group_rule_other_detail:
            group_rule_other_base = {
                "id": group_rule_other_detail.GroupWebsiteHaveRuleOther.rule_other_id,
                "id_rule": group_rule_other_detail.RuleOtherDetailBase.id_rule,
                "description": group_rule_other_detail.RuleOtherDetailBase.description,
                "group_rule_status": group_rule_other_detail.GroupWebsiteHaveRuleOther.group_rule_status

            }
            return group_rule_other_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
        
    def read_group_anti_virus_detail(self, rule_id, group_website_id):
        group_anti_virus_detail = self.session.query(AntiVirusHaveGroupWebsite, AntiVirusBase).outerjoin(AntiVirusBase). \
            filter(AntiVirusHaveGroupWebsite.group_website_id.__eq__(group_website_id)). \
            filter(AntiVirusBase.id.__eq__(rule_id)).first()
        if group_anti_virus_detail:
            group_anti_virus_base = {
                "id": group_anti_virus_detail.AntiVirusHaveGroupWebsite.anti_id,
                "id_rule": group_anti_virus_detail.AntiVirusBase.id_rule,
                "description": group_anti_virus_detail.AntiVirusBase.description,
                "msg": group_anti_virus_detail.AntiVirusBase.msg,
                "tag": group_anti_virus_detail.AntiVirusBase.tag.split(","),
                "group_rule_status": group_anti_virus_detail.AntiVirusHaveGroupWebsite.group_rule_status
            }
            return group_anti_virus_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
    
    def get_dropdown_rule(self):
        db_1 = self.session.query(RuleAvailableBase.rule_available_name)
        db_2 = self.session.query(RuleOtherBase.name)
        db_3 = self.session.query(AntiVirusBase.name)
        dropdown_rule_list = db_1.union(db_2, db_3).all()
        print(dropdown_rule_list)
        all_dropdown_rule_new = []
        for rule in dropdown_rule_list:
            all_dropdown_rule_new.append({'key': rule[0].lower(), 'value': rule[0]})
        return all_dropdown_rule_new

