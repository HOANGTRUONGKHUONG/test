from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from .site_core import SiteConfiguration



class WAFSiteAPI(Resource):
    def __init__(self):
        self.site = SiteConfiguration()
    @jwt_required
    def post(self, id_rule):
        data= request.get_json() or {}
        site_json_data = data["site"]
        return self.site.post_site(site_json_data, id_rule)
    @jwt_required
    def get(self, id_rule):
        return self.site.get_all_site(id_rule)
