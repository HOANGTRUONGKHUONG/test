from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import edit_role_require
from .account_core import Account


class AccountAPI(Resource):
    def __init__(self):
        self.account = Account()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.account.get_all_account(http_parameters)

    @edit_role_require
    def post(self):
        account_json_data = request.get_json()
        return self.account.add_new_account(account_json_data)


class AccountDetailAPI(Resource):
    def __init__(self):
        self.account = Account()

    @jwt_required
    def get(self, account_id):
        return self.account.get_account_detail(account_id)

    @edit_role_require
    def put(self, account_id):
        account_json_data = request.get_json()
        return self.account.edit_account(account_id, account_json_data)

    @edit_role_require
    def delete(self, account_id):
        return self.account.delete_account(account_id)
