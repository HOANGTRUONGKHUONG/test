from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import admin_role_require
from .user_core import User


class UserAPI(Resource):
    def __init__(self):
        self.user = User()

    @admin_role_require
    def get(self):
        http_parameters = request.args.to_dict()
        return self.user.get_all_user(http_parameters)

    @admin_role_require
    def post(self):
        user_json_data = request.get_json()
        return self.user.add_new_user(user_json_data)


class UserDetailAPI(Resource):
    def __init__(self):
        self.user = User()

    @admin_role_require
    def get(self, user_id):
        return self.user.get_user_detail(user_id)

    @admin_role_require
    def put(self, user_id):
        user_json_data = request.get_json()
        return self.user.edit_user(user_id, user_json_data)

    @admin_role_require
    def delete(self, user_id):
        return self.user.delete_user(user_id)


class ProfileAPI(Resource):
    def __init__(self):
        self.pro = User()

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        return self.pro.read_detail_profile(current_user)

    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        json_data = request.get_json()
        return self.pro.edit_profile(current_user, json_data)


class PasswordAPI(Resource):
    def __init__(self):
        self.pwd = User()

    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        json_data = request.get_json()
        return self.pwd.edit_password(current_user, json_data)
