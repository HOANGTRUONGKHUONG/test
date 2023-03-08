from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import admin_role_require
from .check_version_core import CheckVersion
from .licence_core import Licence
from ...libraries.http.response import status_code_200


class LicenceAPI(Resource):
    def __init__(self):
        self.licence = Licence()

    @jwt_required
    def get(self):
        return self.licence.read_current_licence()

    @admin_role_require
    def post(self):
        licence_json_data = request.get_json()
        return self.licence.set_system_licence(licence_json_data)


class VersionCheckAPI(Resource):
    def __init__(self):
        self.version_check = CheckVersion()

    @jwt_required
    def get(self):
        return self.version_check.get_lastest_version()


class VersionDownloadAPI(Resource):
    def __init__(self):
        self.version_download = CheckVersion()

    @jwt_required
    def get(self):
        return self.version_download.download_version()


class VersionUpdateAPI(Resource):
    def __init__(self):
        self.version_update = CheckVersion()

    @jwt_required
    def post(self):
        return self.version_update.update_version()
