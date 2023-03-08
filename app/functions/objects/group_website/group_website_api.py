from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .group_website_core import GroupWebsite


class GroupWebsiteAPI(Resource):
    def __init__(self):
        self.group_website = GroupWebsite()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.group_website.get_all_group_website(http_parameters)

    @jwt_required
    def post(self):
        group_website_json_data = request.get_json()
        return self.group_website.add_new_group_website(group_website_json_data)


class GroupWebsiteDetailAPI(Resource):
    def __init__(self):
        self.group_website = GroupWebsite()

    @jwt_required
    def get(self, group_website_id):
        return self.group_website.get_group_website_detail(group_website_id)

    @jwt_required
    def put(self, group_website_id):
        group_website_json_data = request.get_json()
        return self.group_website.edit_group_website(group_website_id, group_website_json_data)

    @jwt_required
    def delete(self, group_website_id):
        return self.group_website.delete_group_website(group_website_id)

    @jwt_required
    def post(self, group_website_id):
        group_website_json_data = request.get_json()
        return self.group_website.add_or_remove_website_to_group(group_website_id, group_website_json_data)
