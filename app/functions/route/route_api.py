from flask import request
from flask_restful import Resource

from app.functions.route.route_core import Route
from app.libraries.system.decore_permission import admin_role_require


class RouteAPI(Resource):
    def __init__(self):
        self.route = Route()

    @admin_role_require
    def get(self):
        http_parameters = request.args.to_dict()
        return self.route.get_all_route(http_parameters)

    @admin_role_require
    def post(self):
        route_json_data = request.get_json()
        return self.route.add_new_route(route_json_data)


class RouteDetailAPI(Resource):
    def __init__(self):
        self.route = Route()

    @admin_role_require
    def get(self, route_id):
        return self.route.get_route_detail(route_id)

    @admin_role_require
    def put(self, route_id):
        route_json_data = request.get_json()
        return self.route.edit_route(route_id, route_json_data)

    @admin_role_require
    def delete(self, route_id):
        return self.route.delete_route(route_id)
