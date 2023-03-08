from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.web_config import from_database_to_file
from app.libraries.configuration.web_server import modsecurity_group_website_change_waf_status, \
    modsecurity_group_website_rules_change, ngx_reload
from app.libraries.data_format.id_helper import get_id_single_table, get_default_value, advanced_filter
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import WebsiteBase, CRSBase, TrustwaveBase, RuleOtherDetailBase, AntiVirusBase, RuleOtherBase
from app.model import WebsiteHaveCRS, WebsiteHaveTrustwave, WebsiteHaveRuleOther, AntiVirusHaveWebsite
from sqlalchemy import or_

def verify_json_data(json_data):
    verify = ""
    if "website_status" in json_data:
        if json_data["website_status"] not in [1, 0]:
            verify += f"website_status {json_data['website_status']} not validate, "
            
    if "rule_status" in json_data:
        if json_data["rule_status"] not in [1, 0]:
            verify += f"rule_status {json_data['rule_status']} not validate, "
            
    return verify

class WAFWebsiteConfig(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        print("kien:", type(self.session))
        self.logger = c_logger("waf_web_config").log_writer

    def change_waf_status_website(self, website_id, json_data):
        error_code = verify_json_data(json_data)
        if error_code != "":
            self.logger.error(error_code)
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.waf.status.website.fail.client")

        waf_website_detail = self.read_waf_website_detail(website_id)

        if not bool(waf_website_detail):
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.waf.status.website.fail.client")

        self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website_id)).update({"website_status": json_data["website_status"]})
        self.session.query(WebsiteHaveCRS).filter(WebsiteHaveCRS.website_id.__eq__(website_id)).update({"rule_status": json_data["website_status"]})
        self.session.query(WebsiteHaveTrustwave).filter(WebsiteHaveTrustwave.website_id.__eq__(website_id)).update({"rule_status": json_data["website_status"]})
        self.session.query(WebsiteHaveRuleOther).filter(WebsiteHaveRuleOther.website_id.__eq__(website_id)).update({"rule_status": json_data["website_status"]})
        self.session.query(AntiVirusHaveWebsite).filter(AntiVirusHaveWebsite.website_id.__eq__(website_id)).update({"rule_status": json_data["website_status"]})
        try:
            self.session.commit()
            config_status = from_database_to_file()
            if config_status is False:
                self.session.rollback()
            monitor_setting = log_setting(action="WAF", status=1, description="Change WAF status on website")
            ngx_reload()
            return status_code_200("put.waf.status.website.success", self.read_waf_website_detail(website_id))
        except Exception as e:
           
            self.logger.error(f"Change waf status website {website_id} fail, {e}")
            self.session.rollback()

        finally:
            self.session.close()
            self.engine_connect.dispose()
        monitor_setting = log_setting(action="WAF", status=0, description="Change WAF status on website failed")
        return status_code_500("put.waf.status.website.fail.server")

    def read_waf_website_detail(self, website_id):
        waf_status_website_detail = self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website_id)).first()
        if waf_status_website_detail:
            waf_website_base = {
                "website_id": waf_status_website_detail.id,
                "website_name": waf_status_website_detail.website_domain,
                "website_status": waf_status_website_detail.website_status
            }
            return waf_website_base
        else:
            return {}

    def get_all_rule_website(self, http_parameters, website_id):
        if "rule_name" in http_parameters:
            if http_parameters["rule_name"] == "crs":
                del http_parameters['rule_name']
                list_rule_detail, number_of_rule_detail = get_id_single_table(self.session, self.logger,
                                                                            http_parameters, CRSBase)
                print (list_rule_detail)
                
                all_waf_rule_base_data = []
                for rule_detail in list_rule_detail:
                    all_waf_rule_base_data.append(self.read_rule_crs_detail(rule_detail.id, website_id))
                self.session.close()
                self.engine_connect.dispose()
                
            elif http_parameters["rule_name"] == "trustwave":
                del http_parameters['rule_name']
                list_rule_detail, number_of_rule_detail = get_id_single_table(self.session, self.logger,
                                                                            http_parameters, TrustwaveBase)
                
                all_waf_rule_base_data = []
                for rule_detail in list_rule_detail:
                    all_waf_rule_base_data.append(self.read_rule_trust_detail(rule_detail.id, website_id))
                self.session.close()
                self.engine_connect.dispose()
                
            elif http_parameters["rule_name"] == "anti_virus":
                del http_parameters['rule_name']
                list_rule_detail, number_of_rule_detail = get_id_single_table(self.session, self.logger,
                                                                            http_parameters, AntiVirusBase)
                
                all_waf_rule_base_data = []
                for rule_detail in list_rule_detail:
                    all_waf_rule_base_data.append(self.read_anti_virus_detail(rule_detail.id, website_id))
                self.session.close()
                self.engine_connect.dispose()
            
                
            else:
                limit, offset, order = get_default_value(self.logger, http_parameters, RuleOtherDetailBase)
                list_rule_detail = self.session.query(RuleOtherDetailBase.id).outerjoin(WebsiteHaveRuleOther).outerjoin(RuleOtherBase).\
                    filter(WebsiteHaveRuleOther.website_id.__eq__(website_id)).\
                    filter(RuleOtherBase.name.__eq__(http_parameters["rule_name"]))
                
                # search
                if "search" in http_parameters:
                    search_string = http_parameters["search"]
                    base_column = list(RuleOtherDetailBase.__table__.columns)
                    list_rule_detail = list_rule_detail.filter(
                        or_(key.like(f"%{search_string}%") for key in base_column)
                    )
                
                # filter
                list_rule_detail = advanced_filter(http_parameters, self.logger, list_rule_detail, RuleOtherDetailBase)
                # result
                list_rule_detail = list_rule_detail.group_by(RuleOtherDetailBase.id).order_by(order)

                number_of_rule_detail = list_rule_detail.count()
                list_rule_detail = list_rule_detail.limit(limit).offset(offset).all()
                all_waf_rule_base_data = []
                for rule_detail in list_rule_detail:
                    all_waf_rule_base_data.append(self.read_rule_other_detail(rule_detail.id, website_id))
                self.session.close()
                self.engine_connect.dispose()
                
            return get_status_code_200(
                reformat_data_with_paging(all_waf_rule_base_data, number_of_rule_detail,
                                        http_parameters["limit"], http_parameters["offset"]))
            
    def change_rule_of_website_status(self, http_parameters, json_data, rule_id, website_id):
        error_code = verify_json_data(json_data)
        if error_code != "":
            self.logger.error(error_code)
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.waf.rule.status.fail.client")

        if "rule_name" in http_parameters:
           # try:
                if http_parameters["rule_name"] == "crs":
                    rule_detail = self.read_rule_crs_detail(rule_id, website_id)

                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")\
                            
                    self.session.query(WebsiteHaveCRS).\
                        filter(WebsiteHaveCRS.website_id.__eq__(website_id)).\
                        filter(WebsiteHaveCRS.crs_id.__eq__(rule_id)).\
                        update({"rule_status": json_data["rule_status"]})
                        
  
                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
                  #  monitor_setting = log_setting(action="WAF", status=1, description="Change crs rule of website status")
                    ngx_reload()
                    return status_code_200("put.crs.rule.status.success",
                                        self.read_rule_crs_detail(rule_id, website_id)
                                        )
                

                elif http_parameters["rule_name"] == "trustwave":
                    rule_detail = self.read_rule_trust_detail(rule_id, website_id)

                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")

                    self.session.query(WebsiteHaveTrustwave).\
                        filter(WebsiteHaveTrustwave.website_id.__eq__(website_id)).\
                        filter(WebsiteHaveTrustwave.trust_id.__eq__(rule_id)).\
                        update({"rule_status": json_data["rule_status"]})

                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
                    monitor_setting = log_setting(action="WAF", status=1, description="Change trust rule of website status")
                    ngx_reload()
                    return status_code_200("put.trust.rule.status.success",
                                        self.read_rule_trust_detail(rule_id, website_id)
                                        )
                    
                elif http_parameters["rule_name"] == "anti_virus":
                    rule_detail = self.read_anti_virus_detail(rule_id, website_id)
                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")

                    self.session.query(AntiVirusHaveWebsite).\
                        filter(AntiVirusHaveWebsite.website_id.__eq__(website_id)).\
                        filter(AntiVirusHaveWebsite.anti_id.__eq__(rule_id)).\
                        update({"rule_status": json_data["rule_status"]})          
                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
                    monitor_setting = log_setting(action="WAF", status=1, description="Change anti virus of group website status")
                    ngx_reload()
                    return status_code_200("put.anti.virus.status.success",
                                        self.read_anti_virus_detail(rule_id, website_id)
                                        )
                    
                elif http_parameters["rule_name"] == http_parameters["rule_name"]:
                    rule_detail = self.read_rule_other_detail(rule_id, website_id)

                    if not bool(rule_detail):
                        self.session.close()
                        self.engine_connect.dispose()
                        return status_code_400("put.waf.rule.status.fail.client")

                    self.session.query(WebsiteHaveRuleOther).\
                        filter(WebsiteHaveRuleOther.website_id.__eq__(website_id)).\
                        filter(WebsiteHaveRuleOther.rule_other_id.__eq__(rule_id)).\
                        update({"rule_status": json_data["rule_status"]})

                    self.session.commit()
                    config_status = from_database_to_file()
                    if config_status is False:
                        self.session.rollback()
                    monitor_setting = log_setting(action="WAF", status=1, description="Change rule of website status")
                    ngx_reload()
                    return status_code_200("put.waf.rule.status.success",
                                        self.read_rule_other_detail(rule_id, website_id)
                                        )
                else:
                    self.logger.error(f"Change waf rule status {website_id} - rule {rule_id} fail, {e}")
                    self.session.rollback()
                
                    self.session.close()
                    self.engine_connect.dispose()
                    monitor_setting = log_setting(action="WAF", status=1, description="Change rule of website status failed")
                    return status_code_500("put.waf.rule.status.fail.server")
                        
    #         except Exception as e:
    #             self.logger.error(f"Change waf rule status {website_id} - rule {rule_id} fail, {e}")
    #             self.session.rollback()
    #             raise e

    #         finally:
    #             self.session.close()
                # self.engine_connect.dispose()
    #    #     monitor_setting = log_setting(action="WAF", status=1, description="Change rule of website status failed")
    #         return status_code_500("put.waf.rule.status.fail.server")


    def read_rule_crs_detail(self, rule_id, website_id):
        rule_crs_detail = self.session.query(WebsiteHaveCRS, CRSBase).outerjoin(CRSBase). \
                filter(WebsiteHaveCRS.website_id.__eq__(website_id)). \
                filter(CRSBase.id.__eq__(rule_id)).first()

        if rule_crs_detail:
            rule_crs_base = {
                "id": rule_crs_detail.WebsiteHaveCRS.crs_id,
                "id_rule": rule_crs_detail.CRSBase.id_rule,
                "description": rule_crs_detail.CRSBase.description,
                "msg": rule_crs_detail.CRSBase.message,
                "tag": rule_crs_detail.CRSBase.tag.split(","),
                "rule_status": rule_crs_detail.WebsiteHaveCRS.rule_status
            }
            return rule_crs_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
        
    def read_rule_trust_detail(self, rule_id, website_id):
        rule_trust_detail = self.session.query(WebsiteHaveTrustwave, TrustwaveBase).outerjoin(TrustwaveBase). \
                filter(WebsiteHaveTrustwave.website_id.__eq__(website_id)). \
                filter(TrustwaveBase.id.__eq__(rule_id)).first()                                                                                                                                                       
        if rule_trust_detail:
            rule_trust_base = {
                "id": rule_trust_detail.WebsiteHaveTrustwave.trust_id,
                "id_rule": rule_trust_detail.TrustwaveBase.id_rule,
                "msg": rule_trust_detail.TrustwaveBase.message,
                "tag": rule_trust_detail.TrustwaveBase.tag.split(","),
                "rule_status": rule_trust_detail.WebsiteHaveTrustwave.rule_status
            }
            return rule_trust_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
        
        
    def read_rule_other_detail(self, rule_id, website_id):
        rule_other_detail = self.session.query(WebsiteHaveRuleOther, RuleOtherDetailBase).outerjoin(RuleOtherDetailBase). \
                filter(WebsiteHaveRuleOther.website_id.__eq__(website_id)). \
                filter(RuleOtherDetailBase.id.__eq__(rule_id)).first()
                                                                                                                                                                                                                                                                                                                                                                                                                                
        if rule_other_detail:
            rule_other_base = {
                "id": rule_other_detail.WebsiteHaveRuleOther.rule_other_id,
                "id_rule": rule_other_detail.RuleOtherDetailBase.id_rule,
                "description": rule_other_detail.RuleOtherDetailBase.description,
                "rule_status": rule_other_detail.WebsiteHaveRuleOther.rule_status

            }
            return rule_other_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
        
    def read_anti_virus_detail(self, rule_id, website_id):
        anti_virus_detail = self.session.query(AntiVirusHaveWebsite, AntiVirusBase).outerjoin(AntiVirusBase). \
            filter(AntiVirusHaveWebsite.website_id.__eq__(website_id)). \
            filter(AntiVirusBase.id.__eq__(rule_id)).first()
        if anti_virus_detail:
            anti_virus_base = {
                "id":anti_virus_detail.AntiVirusHaveWebsite.anti_id,
                "id_rule": anti_virus_detail.AntiVirusBase.id_rule,
                "description": anti_virus_detail.AntiVirusBase.description,
                "msg": anti_virus_detail.AntiVirusBase.msg,
                "tag": anti_virus_detail.AntiVirusBase.tag.split(","),
                "rule_status": anti_virus_detail.AntiVirusHaveWebsite.rule_status
            }
            return anti_virus_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
    
   
