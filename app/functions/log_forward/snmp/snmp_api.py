from flask_restful import Resource
from flask import request
from app.libraries.system.decore_permission import admin_role_require
from flask_jwt_extended import jwt_required
from app.functions.log_forward.log_forward_collections import LogForwardCollections
from app.functions.log_forward.snmp.snmp_core import SNMPForward


class SNMPCollectionsAPI(Resource):
    def __init__(self):
        self.collections = LogForwardCollections()

    def options(self):
        return self.collections.snmp_collections()


class SNMPConfigAPI(Resource):
    def __init__(self):
        self.snmp_config = SNMPForward()

    @jwt_required
    def get(self):
        return self.snmp_config.read_config()

    @admin_role_require
    def post(self):
        json_data = request.get_json()
        return self.snmp_config.snmp_config_info(json_data)


class SNMPCommunityAPI(Resource):
    def __init__(self):
        self.snmp_config = SNMPForward()

    @admin_role_require
    def post(self):
        json_data = request.get_json()
        return self.snmp_config.add_snmp_community(json_data)


class SNMP3CommunityAPI(Resource):
    def __init__(self):
        self.snmp_config = SNMPForward()

    @admin_role_require
    def post(self):
        json_data = request.get_json()
        return self.snmp_config.add_snmp_v3_community(json_data)


class SNMPCommunityDetailAPI(Resource):
    def __init__(self):
        self.snmp_config = SNMPForward()

    @jwt_required
    def get(self, community_name):
        return self.snmp_config.read_snmp_community_detail(community_name)

    @admin_role_require
    def put(self, community_name):
        json_data = request.get_json()
        return self.snmp_config.edit_snmp_community_detail(community_name, json_data)

    @admin_role_require
    def delete(self, community_name):
        return self.snmp_config.delete_snmp_community(community_name)


class SNMP3CommunityDetailAPI(Resource):
    def __init__(self):
        self.snmp_config = SNMPForward()

    @jwt_required
    def get(self, community_name):
        return self.snmp_config.read_snmp_community_v3_detail(community_name)

    @admin_role_require
    def put(self, community_name):
        json_data = request.get_json()
        return self.snmp_config.edit_snmp_community_v3_detail(community_name, json_data)

    @admin_role_require
    def delete(self, community_name):
        return self.snmp_config.delete_snmp_community(community_name)
