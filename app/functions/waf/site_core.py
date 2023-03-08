from app.model import  ExceptionBase
from app.libraries.logger import c_logger
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import *
import re
from app.libraries.configuration.web_server import *

class SiteConfiguration(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        # self.logger = c_logger("test").log_writer
    
    def post_site(self, site_data ,id_rule):
        try:
        # print(site_data)
            check_id_rule = self.session.query(ExceptionBase).filter(ExceptionBase.id_rule.__eq__(id_rule)).first()
        # print(check_website_id)
            if check_id_rule:
                for site in site_data:
                    if site[0]!="/" or str(site_data).count('/')!=len(site_data):
                        return status_code_400("Wrong.position.or.missing.'/'")
                check_id_rule.sites= set(site_data)
                self.session.commit()
            else:
                return status_code_400("rule.not.found")
        except Exception as e:
            return status_code_400(e)
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("update.site.success",list(set(site_data)))

    def get_all_site(self, id_rule):
        try:
            data_rule_site = self.session.query(ExceptionBase).filter(ExceptionBase.id_rule.__eq__(id_rule)).first()
            if data_rule_site:
                if data_rule_site.sites == "":
                    return status_code_200("success",[]) 
                sites = data_rule_site.sites.split(',')
                # site = re.sub(r"[^a-zA-Z0-9,/]","",str(sorted(set(sites)))).split(',')
            # print(type(sites))
                return status_code_200("success",sites)
                
            else:
                return status_code_400("rule.not.found")        
        except Exception as e:
            return status_code_400(e)        
        finally:
            self.session.close()
            self.engine_connect.dispose()