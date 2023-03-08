from flask import request
from flask_restful import Resource

from app.libraries.system.decore_permission import edit_role_require
from .diagnostic_core import Diagnostic


class PingAPI(Resource):
    def __init__(self):
        self.diagnostic = Diagnostic()

    @edit_role_require
    def post(self):
        ping_json = request.get_json()
        return self.diagnostic.ping(ping_json)


class TraceRouteAPI(Resource):
    def __init__(self):
        self.diagnostic = Diagnostic()

    @edit_role_require
    def post(self):
        trace_route_json = request.get_json()
        return self.diagnostic.trace_route(trace_route_json)


class PortCheckAPI(Resource):
    def __init__(self):
        self.diagnostic = Diagnostic()

    @edit_role_require
    def post(self):
        port_check_json = request.get_json()
        return self.diagnostic.port_check(port_check_json)
