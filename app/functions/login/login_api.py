from flask import request
from flask_jwt_extended import jwt_required, jwt_refresh_token_required, get_jwt_identity
from flask_restful import Resource

from app.functions.user.user_core import User
from .login_core import Login


class LoginAPI(Resource):
    def __init__(self):
        self.login = Login()

    def post(self):
        input_json_data = request.get_json()
        return self.login.login(input_json_data)


class LogoutAccessAPI(Resource):
    def __init__(self):
        self.login = Login()

    @jwt_required
    def delete(self):
        return self.login.logout_access_token()


class LogoutRefreshAPI(Resource):
    def __init__(self):
        self.login = Login()

    @jwt_refresh_token_required
    def delete(self):
        return self.login.logout_refresh_token()


class SignupAPI(Resource):
    def __init__(self):
        self.user = User()

    def post(self):
        user_json_data = request.get_json()
        self.user.add_new_user(user_json_data)


class RefreshAccessTokenAPI(Resource):
    def __init__(self):
        self.login = Login()

    @jwt_refresh_token_required
    def get(self):
        return self.login.refresh_user_token()


class TwoFactorAuthentication(Resource):
    def __init__(self):
        self.login = Login()

    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        return self.login.create_two_factor_authentication(current_user)

    @jwt_required
    def post(self):
        current_user = get_jwt_identity()
        input_json_data = request.get_json()
        return self.login.turn_on_two_factor_authentication(input_json_data, current_user)

    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        input_json_data = request.get_json()
        return self.login.turn_off_two_factor_authentication(input_json_data, current_user)
