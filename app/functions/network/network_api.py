from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .network_collections import NetworkCollections
from .network_core import NetworkConfiguration


class NetworkAPI(Resource):
    def __init__(self):
        self.network = NetworkConfiguration()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.network.get_all_interface(http_parameters)


class NetworkDetailAPI(Resource):
    def __init__(self):
        self.network = NetworkConfiguration()

    @jwt_required
    def get(self, interface_name):
        return self.network.get_config_detail(interface_name, 'ethernets')

    @jwt_required
    def put(self, interface_name):
        json_data = request.get_json()
        return self.network.edit_config_setting(interface_name, json_data, 'ethernets')

    @jwt_required
    def delete(self, interface_name):
        return self.network.flush_config_setting(interface_name, 'ethernets')


class PhysicalInterfaceAPI(Resource):
    def __init__(self):
        self.collections = NetworkCollections()

    def options(self):
        return self.collections.physical_interface_collections()


class VirtualInterfaceAPI(Resource):
    def __init__(self):
        self.collections = NetworkCollections()

    def options(self):
        return self.collections.virtual_interface_collections()


class VirtualNetworkBondAPI(Resource):
    def __init__(self):
        self.virtual_network_bond = NetworkConfiguration()

    @jwt_required
    def post(self):
        json_data = request.get_json()
        return self.virtual_network_bond.add_new_config_setting(json_data, 'bonds')

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.virtual_network_bond.get_all_virtual_interface(http_parameters, 'bonds')


class VirtualNetworkBondDetailAPI(Resource):
    def __init__(self):
        self.virtual_network_bond = NetworkConfiguration()

    @jwt_required
    def get(self, bond_name):
        return self.virtual_network_bond.get_config_detail(bond_name, 'bonds')

    @jwt_required
    def put(self, bond_name):
        json_data = request.get_json()
        return self.virtual_network_bond.edit_config_setting(bond_name, json_data, 'bonds')

    @jwt_required
    def delete(self, bond_name):
        return self.virtual_network_bond.flush_config_setting(bond_name, 'bonds')


class VirtualNetworkBridgesAPI(Resource):
    def __init__(self):
        self.virtual_network_bridges = NetworkConfiguration()

    @jwt_required
    def post(self):
        json_data = request.get_json()
        return self.virtual_network_bridges.add_new_config_setting(json_data, 'bridges')

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.virtual_network_bridges.get_all_virtual_interface(http_parameters, 'bridges')


class VirtualNetworkBridgesDetailAPI(Resource):
    def __init__(self):
        self.virtual_network_bridges = NetworkConfiguration()

    @jwt_required
    def get(self, bridges_name):
        return self.virtual_network_bridges.get_config_detail(bridges_name, 'bridges')

    @jwt_required
    def put(self, bridges_name):
        json_data = request.get_json()
        return self.virtual_network_bridges.edit_config_setting(bridges_name, json_data, 'bridges')

    @jwt_required
    def delete(self, bridges_name):
        return self.virtual_network_bridges.flush_config_setting(bridges_name, 'bridges')
