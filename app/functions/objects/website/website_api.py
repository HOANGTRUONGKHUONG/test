from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .website_core import Website


class WebsiteAPI(Resource):
    def __init__(self):
        self.website = Website()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.website.get_all_website(http_parameters)

    @jwt_required
    def post(self):
        website_json_data = request.get_json()
        return self.website.add_new_website(website_json_data)


class WebsiteDetailAPI(Resource):
    def __init__(self):
        self.website = Website()

    @jwt_required
    def get(self, website_id):
        return self.website.get_website_detail(website_id)

    @jwt_required
    def put(self, website_id):
        website_json_data = request.get_json()
        return self.website.edit_website(website_id, website_json_data)

    @jwt_required
    def delete(self, website_id):
        return self.website.delete_website(website_id)


class ClearCachingAPI(Resource):
    def __init__(self):
        self.website = Website()

    @jwt_required
    def delete(self, website_id):
        return self.website.clear_caching_detail(website_id)
