from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import edit_role_require
from .high_availability_core import HighAvailability


class HighAvailabilityAPI(Resource):
    def __init__(self):
        self.ha = HighAvailability()

    @jwt_required
    def get(self):
        return self.ha.get_ha_config()

    @edit_role_require
    def post(self):
        ha_json_data = request.get_json()
        return self.ha.create_new_ha(ha_json_data)

    @edit_role_require
    def put(self):
        ha_json_data = request.get_json()
        return self.ha.edit_ha_config(ha_json_data)

    @edit_role_require
    def delete(self):
        return self.ha.remove_ha_config()


class HighAvailabilityModeAPI(Resource):
    def __init__(self):
        self.ha = HighAvailability()

    @jwt_required
    def get(self):
        return self.ha.list_ha_mode()
