from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import edit_role_require
from .waf_alert_core import WAFAlertConfiguration
from .waf_core import WAFConfiguration
from .waf_web_core import WAFWebsiteConfig


class WebApplicationFirewallAPI(Resource):
    def __init__(self):
        self.waf = WAFConfiguration()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.waf.get_all_waf_group(http_parameters)


class WebApplicationFirewallDetailAPI(Resource):
    def __init__(self):
        self.waf = WAFConfiguration()

    @jwt_required
    def get(self, group_website_id):
        return self.waf.get_waf_group_detail(group_website_id)

    @edit_role_require
    def put(self, group_website_id):
        json_data = request.get_json()
        return self.waf.change_waf_group_website_status(group_website_id, json_data)

class WAFWebsiteAPI(Resource):
    def __init__(self):
        self.waf_web = WAFWebsiteConfig()

    @edit_role_require
    def put(self, website_id):
        json_data = request.get_json()
        return self.waf_web.change_waf_status_website(website_id, json_data)

class WebApplicationFirewallRuleAPI(Resource):
    def __init__(self):
        self.waf = WAFConfiguration()

    @jwt_required
    def get(self, group_website_id):
        http_parameters = request.args.to_dict()
        return self.waf.get_all_rule_group(http_parameters, group_website_id)

class WebApplicationFirewallRuleDetail(Resource):
    def __init__(self):
        self.waf = WAFConfiguration()

    @edit_role_require
    def put(self, rule_id, group_website_id):
        json_data = request.get_json()
        http_parameters = request.args.to_dict()
        return self.waf.change_rule_of_group_website_status(http_parameters, json_data, rule_id, group_website_id)

class WebsiteWAFRuleAPI(Resource):
    def __init__(self):
        self.waf_web = WAFWebsiteConfig()

    @jwt_required
    def get(self, website_id):
        http_parameters = request.args.to_dict()
        return self.waf_web.get_all_rule_website(http_parameters, website_id)


class WebsiteWAFRuleDetail(Resource):
    def __init__(self):
        self.waf_web = WAFWebsiteConfig()

    @edit_role_require
    def put(self, rule_id, website_id):
        json_data = request.get_json()
        http_parameters = request.args.to_dict()
        return self.waf_web.change_rule_of_website_status(http_parameters, json_data, rule_id, website_id)

class WAFDropDownAPI(Resource):
    def __init__(self):
        self.waf = WAFConfiguration()

    @jwt_required
    def get(self):
        return self.waf.get_dropdown_rule()
    

# class WebApplicationFirewallRuleDetail(Resource):
#     def __init__(self):
#         self.waf = WAFConfiguration()

#     @jwt_required
#     def get(self, group_website_id, group_rule_id):
#         return self.waf.get_waf_rule_of_website_detail(group_website_id, group_rule_id)

#     @edit_role_require
#     def put(self, group_website_id, group_rule_id):
#         json_data = request.get_json()
#         return self.waf.change_group_rule_of_website_status(group_website_id, group_rule_id, json_data)


class WebApplicationFirewallAlert(Resource):
    def __init__(self):
        self.waf_alert = WAFAlertConfiguration()

    @jwt_required
    def get(self, group_website_id):
        return self.waf_alert.get_group_website_alert_detail(group_website_id)

    @edit_role_require
    def put(self, group_website_id):
        json_data = request.get_json()
        return self.waf_alert.change_group_website_alert(group_website_id, json_data)
