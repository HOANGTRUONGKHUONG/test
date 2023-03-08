from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import edit_role_require
from .about_core import About


class AboutAPI(Resource):
    def __init__(self):
        self.about = About()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.about.read_system_information(http_parameters)

    @edit_role_require
    def post(self):
        system_json_data = request.get_json()
        return self.about.set_system_name(system_json_data)
