from flask_restful import Resource
from flask import request
from app.libraries.system.decore_permission import admin_role_require
from flask_jwt_extended import jwt_required
from app.functions.log_forward.log_forward_collections import LogForwardCollections
from app.functions.log_forward.syslog.syslog_core import SyslogForward


class SyslogAPI(Resource):
    def __init__(self):
        self.collections = LogForwardCollections()
        self.syslog_forward = SyslogForward()

    @jwt_required
    def get(self):
        return self.syslog_forward.read_config()

    @admin_role_require
    def post(self):
        syslog_json_data = request.get_json()
        return self.syslog_forward.change_config(syslog_json_data)

    @admin_role_require
    def delete(self):
        return self.syslog_forward.remove_config()

    def options(self):
        return self.collections.syslog_collections()


class SeverityAPI(Resource):
    def __init__(self):
        self.collections = LogForwardCollections()

    def options(self):
        return self.collections.severity_collections()


class FacilityAPI(Resource):
    def __init__(self):
        self.collections = LogForwardCollections()

    def options(self):
        return self.collections.facility_collections()


class LogTypeAPI(Resource):
    def __init__(self):
        self.collections = LogForwardCollections()

    def options(self):
        return self.collections.log_type()


class SyslogTestAPI(Resource):
    def __init__(self):
        self.syslog_test = SyslogForward()

    @admin_role_require
    def post(self):
        syslog_json_data = request.get_json()
        return self.syslog_test.test_connection(syslog_json_data)
