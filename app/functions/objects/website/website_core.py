import os
import shutil
import requests

from sqlalchemy import or_

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.web_server import ngx_website_config, ngx_config_remove_backup, ngx_remove_config, \
    ngx_config_rollback, ngx_config_backup, ngx_reload, dump_ips_config, generate_ips_config_data, \
    ngx_add_website_to_group_website, active_health_check
from app.libraries.data_format.id_helper import get_default_value
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.validate_data import *
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import WebsiteListenBase, WebsiteUpstreamBase, SSLBase, WebsiteBase, ActiveHealthCheckBase
from app.model import CRSBase, TrustwaveBase, RuleOtherDetailBase, AntiVirusBase
from app.model import WebsiteHaveCRS, WebsiteHaveTrustwave, WebsiteHaveRuleOther, AntiVirusHaveWebsite

def verify_json_data(json_data):
    verify = ""
    if "website_domain" in json_data and not is_domain(json_data["website_domain"]):
        verify += f"domain {json_data['website_domain']} not true, "
    if "upstream" in json_data:
        for upstream_item in json_data["upstream"]:
            if not is_ipv4(str(upstream_item["ip"])) and not is_ipv6(str(upstream_item["ip"])):
                verify += f"ip {upstream_item['ip']} is not true, "
            if not is_port(str(upstream_item["port"])):
                verify += f"port {upstream_item['port']} is not true, "
            if upstream_item["type"] not in ["main", "backup", "load balancing"]:
                verify += f"port type {upstream_item['type']} not true, "
    else:
        verify += "upstream not true, "
    if "listened" in json_data:
        if not is_port(str(json_data["listened"]["main"])):
            verify += f"port_listen main {json_data['listened']['main']} is not true, "
        for port in json_data["listened"]["redirect"]:
            if not is_port(str(port)):
                verify += f"port_listen redirect {port} is not true, "
    else:
        verify += "port_listen not true, "

    if "health_check_status" in json_data:
        if json_data["health_check_status"] not in [1, 0]:
            verify += f"health_check_status {json_data['health_check_status']} not validate, "
            
    if "website_status" in json_data:
        if json_data["website_status"] not in [1, 0]:
            verify += f"website_status {json_data['website_status']} not validate, "

    if "health_check_infor" in json_data and "health_check_status" in json_data:
        if json_data["health_check_status"]==1:
            for status in json_data["health_check_infor"]["valid_statuses"]:
                if int(status) < 100 or int(status) > 599:
                    verify += "valid_statuses not true, "

    
    return verify


class Website(object):
    def __init__(self):
       # self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("website").log_writer

    def get_all_website(self, http_parameters):
        self.session,self.engine_connect = ORMSession_alter()
        limit, offset, order = get_default_value(self.logger, http_parameters, WebsiteBase)

        list_website_id = self.session.query(WebsiteBase.id). \
            outerjoin(WebsiteListenBase).outerjoin(WebsiteUpstreamBase)

        # optional parameter
        if "available" in http_parameters and http_parameters["available"] == "1":
            list_website_id = list_website_id.filter(WebsiteBase.group_website_id.__eq__(None))
        if "search" in http_parameters:
            search_string = http_parameters["search"]
            base_column = list(WebsiteBase.__table__.columns)
            listen_column = list(WebsiteListenBase.__table__.columns)
            upstream_column = list(WebsiteUpstreamBase.__table__.columns)
            list_column = base_column + listen_column + upstream_column
            list_website_id = list_website_id.filter(
                or_(key.like(f"%{search_string}%") for key in list_column)
            )

        # group result
        list_website_id = list_website_id.group_by(WebsiteBase.id).order_by(order)
        # get final result
        number_of_website = list_website_id.count()
        list_website_id = list_website_id.limit(limit).offset(offset).all()
        # read result
        all_website_base_data = []
        for web_id in list_website_id:
            all_website_base_data.append(self.read_website_detail(web_id.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(all_website_base_data, number_of_website, limit, offset))

    def add_new_website(self, website_json_data):
        self.session,self.engine_connect = ORMSession_alter()
        json_error = verify_json_data(website_json_data)
        if json_error:
            self.logger.error(f"Json data error, {json_error}")
            return status_code_400("post.website.fail.client")
        ngx_config_backup()
        website_obj = WebsiteBase(website_domain=website_json_data["website_domain"], cache=website_json_data["cache"],
                                  active=website_json_data["active"], website_status=0,
                                  health_check_status=website_json_data["health_check_status"])
        self.session.add(website_obj)
        self.session.flush()
        self.insert_port_to_db(website_obj.id, website_json_data)

        # add rule detail with website
        list_rule_crs = self.session.query(CRSBase.id).all()
        for rule_crs in list_rule_crs:
            crs_detail = WebsiteHaveCRS(website_id=website_obj.id, crs_id=rule_crs.id, rule_status=1)
            self.session.add(crs_detail)
        self.session.flush()

        list_rule_trust = self.session.query(TrustwaveBase.id).all()
        for rule_trust in list_rule_trust:
            trust_detail = WebsiteHaveTrustwave(website_id=website_obj.id, trust_id=rule_trust.id, rule_status=1)
            self.session.add(trust_detail)
        self.session.flush()

        list_rule_other = self.session.query(RuleOtherDetailBase.id).all()
        for rule_other in list_rule_other:
            other_detail = WebsiteHaveRuleOther(website_id=website_obj.id, rule_other_id=rule_other.id, rule_status=1)
            self.session.add(other_detail)
        self.session.flush()
        
        list_anti_virus = self.session.query(AntiVirusBase.id).all()
        for anti_virus in list_anti_virus:
            anti_virus_detail = AntiVirusHaveWebsite(website_id=website_obj.id, anti_id=anti_virus.id, rule_status=1)
            self.session.add(anti_virus_detail)
        self.session.flush()

        # # core
        config_success = ngx_website_config(domain=website_json_data["website_domain"],
                                            list_upstream=website_json_data["upstream"],
                                            listened=website_json_data["listened"],
                                            cache=website_json_data["cache"])
                
        if config_success:
            # db
            try:
                self.session.commit()
                active_health_check()
                ngx_config_remove_backup()
                ngx_reload()
                
                a = log_setting(action="Website", status=1, description="Add new website")
                data = self.read_website_detail(website_obj.id)
                return status_code_200("post.website.success", data)
            except Exception as e:
                raise e
                self.session.rollback()
                self.logger.error(f"Add website fail, {e}")
                a = log_setting(action="Website", status=0, description="Add new website failed")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        ngx_config_rollback()
        return status_code_500("post.website.fail.server")

    def insert_port_to_db(self, website_id, website_json_data):
        # upstream
        for upstream_item in website_json_data["upstream"]:
            if upstream_item["protocol"] == "HTTPS":
                upstream_obj = WebsiteUpstreamBase(website_id=website_id, ip=upstream_item["ip"], ssl=upstream_item["ssl"]["id"],
                                                port=upstream_item["port"], type=upstream_item["type"], protocol=upstream_item["protocol"])
            else:
                upstream_obj = WebsiteUpstreamBase(website_id=website_id, ip=upstream_item["ip"],
                                                port=upstream_item["port"], type=upstream_item["type"], protocol=upstream_item["protocol"])
            self.session.add(upstream_obj)

        # listen
        port_redirect = ",".join(str(port) for port in website_json_data["listened"]["redirect"])
        if website_json_data["listened"]["protocol"] == "HTTPS":
            listen_main_obj = WebsiteListenBase(website_id=website_id, ssl=website_json_data["listened"]["ssl_id"], redirect=port_redirect,
                                                main=website_json_data["listened"]["main"], protocol=website_json_data["listened"]["protocol"])
        else:
            listen_main_obj = WebsiteListenBase(website_id=website_id, redirect=port_redirect,
                                                main=website_json_data["listened"]["main"], protocol=website_json_data["listened"]["protocol"])
        self.session.add(listen_main_obj)
        
        # active_health_check
        if website_json_data["health_check_status"]==1:

            valid_statuses = ",".join(str(status) for status in website_json_data["health_check_infor"]["valid_statuses"])
            health_check_obj = ActiveHealthCheckBase(website_id=website_id, size=website_json_data["health_check_infor"]["size"],
                                                        url=website_json_data["health_check_infor"]["url"],
                                                        port_check=website_json_data["health_check_infor"]["port_check"],
                                                        interval=website_json_data["health_check_infor"]["interval"],
                                                        timeout=website_json_data["health_check_infor"]["timeout"], 
                                                        fall=website_json_data["health_check_infor"]["fall"],
                                                        rise=website_json_data["health_check_infor"]["rise"], 
                                                        valid_statuses=valid_statuses,
                                                        concurrency=website_json_data["health_check_infor"]["concurrency"])  
            self.session.add(health_check_obj)

        self.session.flush()
        return True

    def get_website_detail(self, website_id):
        self.session,self.engine_connect = ORMSession_alter()
        website_detail = self.read_website_detail(website_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(website_detail):
            return get_status_code_200(website_detail)
        else:
            return status_code_400("get.website.detail.fail.client")

    def edit_website(self, website_id, website_json_data):
        self.session,self.engine_connect = ORMSession_alter()
        if "redirect" in website_json_data:
            for i in range(len(website_json_data['redirect'])):
                if website_json_data['redirect'][i] == "":
                    del website_json_data['redirect'][i]
        ngx_config_backup()
        website_detail = self.read_website_detail(website_id)
        website_old_domain = website_detail["website_domain"]
        website_detail.update(website_json_data)
        # try delete old listen, upstream and insert new value to verify
        try:
            self.session.query(WebsiteUpstreamBase).filter(WebsiteUpstreamBase.website_id.__eq__(website_id)).delete()
            self.session.query(WebsiteListenBase).filter(WebsiteListenBase.website_id.__eq__(website_id)).delete()
            self.session.query(ActiveHealthCheckBase).filter(ActiveHealthCheckBase.website_id.__eq__(website_id)).delete()
            self.insert_port_to_db(website_id, website_detail)
            # get old website detail and update new value
            website_obj = self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website_id)).first()
            website_obj.website_domain = website_detail["website_domain"]
            website_obj.cache = website_detail["cache"]
            website_obj.active = website_detail["active"]
            website_obj.health_check_status = website_detail["health_check_status"]
            self.session.flush()
        except Exception as e:
            self.logger.error(e)
            return status_code_400("put.website.fail.client")

        # core
        # remove config
        if not ngx_remove_config(website_old_domain):
            # pass
            return status_code_400("put.website.fail.client")
        # add new config with update
        config_success = ngx_website_config(domain=website_detail["website_domain"],
                                            list_upstream=website_detail["upstream"],
                                            listened=website_detail["listened"],
                                            cache=website_detail["cache"])
        if config_success:
            if website_obj.group_website_id is not None:
                ngx_add_website_to_group_website(website_obj.website_domain, website_obj.group_website_id)
            config_data = generate_ips_config_data(self.session, website_detail["website_domain"])
            dump_ips_config(config_data)
            # db
            try:
                self.session.commit()
                active_health_check()
                ngx_config_remove_backup()
                ngx_reload()
                a = log_setting(action="Website", status=1, description="Edit website")
                data = self.read_website_detail(website_id)
                # if data==False:
                #     return status_code_400("put.website.wait.health_check")
                return status_code_200("put.website.success", data)
            except Exception as e:
                self.session.rollback()
                self.logger.error(f"Edit website fail, {e}")
                a = log_setting(action="Website", status=0, description="Edit website failed")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        ngx_config_rollback()
        return status_code_500("put.website.fail.server")

    def delete_website(self, website_id):
        self.session,self.engine_connect = ORMSession_alter()
        website_detail = self.read_website_detail(website_id)
        print("ho ai hai:", website_detail)
        try:
            self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website_id)).delete()
        except Exception as e:
            self.logger.error(e)
            return status_code_400("delete.website.fail.client")
        ngx_config_backup()
        # core
        remove_success = ngx_remove_config(website_detail["website_domain"])
        if remove_success:
            # db
            try:
                self.session.commit()
                active_health_check()
                ngx_config_remove_backup()
                ngx_reload()
                a = log_setting(action="Website", status=1, description="Delete website")
                return status_code_200("delete.website.success", {})
            except Exception as e:
                #raise e
                self.session.rollback()
                self.logger.error(f"Delete website fail, {e}")
                a = log_setting(action="Website", status=0, description="Delete website failed")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        ngx_config_rollback()
        return status_code_500(f"delete.website.fail.server")

    def clear_caching_detail(self, website_id):
        self.session,self.engine_connect = ORMSession_alter()
        list_web = self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website_id)).first()

        if list_web:
            # Ghep link bang thu vien os.path.join(path, "...")
            link = os.path.join("/tmp", list_web.website_domain)
            try:
                if os.path.exists(link):
                    for link_file in os.listdir(link):
                        path_link = os.path.join(link, link_file)
                        if os.path.exists(path_link):
                            shutil.rmtree(path_link)
                    self.logger.error(f"Clear caching website detail success!, {list_web.website_domain}")
                    return status_code_200(f"Clear.cache.site.{list_web.website_domain}.success!", {})
            except Exception as e:
                self.logger.error(f"Clear cache fail, {e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()
            self.logger.error(f"Clear cache website detail error, {list_web.website_domain}")
            return status_code_500(f"Clear.caching.fail.server")
        else:
            self.logger.error(f"Query website detail error, {list_web.website_domain}")
            return status_code_400("Website.is.not.exit!")

    def read_website_detail(self, website_id):
        self.session,self.engine_connect = ORMSession_alter()
        website_detail = self.session.query(WebsiteBase, SSLBase).outerjoin(SSLBase). \
            filter(WebsiteBase.id.__eq__(website_id)).first()
        if website_detail:
            website_base_data = {
                "id": website_detail.WebsiteBase.id,
                "website_domain": website_detail.WebsiteBase.website_domain,
                "upstream": [],
                "cache": website_detail.WebsiteBase.cache,
                "listened": {},
                "active": website_detail.WebsiteBase.active,
                "health_check_status": website_detail.WebsiteBase.health_check_status,
                "health_check_infor": {}
               
            }
            listen_detail = self.session.query(WebsiteListenBase). \
                filter(WebsiteListenBase.website_id.__eq__(website_id)).first()
            if listen_detail:
                website_base_data["listened"]["main"] = listen_detail.main
                website_base_data["listened"]["redirect"] = listen_detail.redirect.split(",")
                website_base_data["listened"]["protocol"] = listen_detail.protocol
                website_base_data["listened"]["ssl"] = {}
                if listen_detail.protocol == "HTTPS":
                    ssl_detail = self.session.query(SSLBase). \
                        filter(SSLBase.id.__eq__(listen_detail.ssl)).first()
                    if ssl_detail:
                        website_base_data["listened"]["ssl"]["id"] = ssl_detail.id
                        website_base_data["listened"]["ssl"]["name"] = ssl_detail.ssl_name
            else:
                self.logger.error(f"Query listen error, {listen_detail}")

            health_check_detail = self.session.query(ActiveHealthCheckBase).\
                filter(ActiveHealthCheckBase.website_id.__eq__(website_id)).first()
            if health_check_detail:
                website_base_data["health_check_infor"]["size"] = health_check_detail.size
                website_base_data["health_check_infor"]["url"] = health_check_detail.url
                website_base_data["health_check_infor"]["port_check"] = health_check_detail.port_check
                website_base_data["health_check_infor"]["interval"] = health_check_detail.interval 
                website_base_data["health_check_infor"]["timeout"] = health_check_detail.timeout
                website_base_data["health_check_infor"]["fall"] = health_check_detail.fall 
                website_base_data["health_check_infor"]["rise"] = health_check_detail.rise 
                website_base_data["health_check_infor"]["valid_statuses"] = health_check_detail.valid_statuses.split(",")
                website_base_data["health_check_infor"]["concurrency"] = health_check_detail.concurrency     
                  
            else:
                self.logger.error(f"Query health_check error, {health_check_detail}")

            upstream_detail = self.session.query(WebsiteUpstreamBase). \
                filter(WebsiteUpstreamBase.website_id.__eq__(website_id)).all()
            if upstream_detail:
                for upstream in upstream_detail:
                    ups = {
                        "ip": upstream.ip,
                        "port": upstream.port,
                        "type": upstream.type,
                        "protocol": upstream.protocol,
                        "ssl": {},
                        "status_check": ""
                    }
                    if upstream.protocol == "HTTPS":
                        ssl_detail = self.session.query(SSLBase). \
                            filter(SSLBase.id.__eq__(upstream.ssl)).first()
                        if ssl_detail:
                            ups["ssl"]["id"] = ssl_detail.id
                            ups["ssl"]["name"] = ssl_detail.ssl_name

                    if website_base_data["health_check_status"]==1:
                        check = self.get_status_health_check(website_id)
                        if check=={}:
                            ups["status_check"] = "DOWN"
                        elif check and check[upstream.ip] is True:
                            ups["status_check"] = "UP" 
                        else:
                            ups["status_check"] = "DOWN"                           

                    website_base_data["upstream"].append(ups)
            else:
                self.logger.error(f"Query upstream error, {upstream_detail}")
            self.session.close()
            self.engine_connect.dispose()
            return website_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            self.logger.error(f"Query website detail error, {website_detail}")
            return {}

    def get_status_health_check(self, website_id):
        self.session,self.engine_connect = ORMSession_alter()
        web_detail = self.session.query(WebsiteBase).filter(WebsiteBase.id.__eq__(website_id)).first()
        domain = web_detail.website_domain
      #  print("maiL  :", domain)
        r = requests.get("http://localhost/health-check-status")
    #    print("lalalalala:  ", r.text)
        data = r.text.split("\n")
     #   print("hehehehhehe:", data)
        form = []
        flag = 0
        try:
            for line in data:
                upstream = f"upstream_{domain}"       
                if upstream in line:
                    flag = 1
                if flag==1:
                    form.append(line)  
                if line=="":
                    pass
                if line=="" and flag==1:
                    break

            result = {}
            
            for line in form:
                ups_detail = self.session.query(WebsiteUpstreamBase.ip).filter(WebsiteUpstreamBase.website_id.__eq__(website_id)).all()
                for web_infor in ups_detail:
                    if web_infor.ip in line:
                        if "up" in line:
                            result[web_infor.ip]=True
                        else:
                            result[web_infor.ip]=False
         #   print("result:", result)
            return result
        except Exception as e:
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("no.check.heathcheck")
       
                        