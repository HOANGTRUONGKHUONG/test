import glob
import os

from app.functions.monitors.traffic.monitor_traffic_service import get_list_interface
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.netplan_config_manager import NetplanConfigManager
from app.libraries.configuration.network import network_config_backup, \
    network_config_rollback, network_config_remove_backup, network_config_apply, \
    read_interface_information
from app.libraries.data_format.network_calculator import get_ip_address, get_netmask_bits
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.string_format import dict_to_list, string_to_json
from app.libraries.data_format.validate_data import is_ipv4, is_ipv6, is_ipv4_subnet, is_ipv6_subnet
from app.libraries.http.response import *
from app.libraries.inout.file import write_yaml_file_from_object, parsed_json
from app.libraries.logger import c_logger
# from app.libraries.system.interface_check import get_list_interface
from app.libraries.system.log_action import log_setting
from app.setting import NETWORK_CONFIG_DIR


def get_file_location():
    names_to_paths = {}
    prefix = NETWORK_CONFIG_DIR
    for yaml_dir in ['lib', 'etc', 'run']:
        for yaml_file in glob.glob(os.path.join(prefix, yaml_dir, 'netplan', '*.yaml')):
            names_to_paths[os.path.basename(yaml_file)] = yaml_file

    files = [names_to_paths[name] for name in sorted(names_to_paths.keys())]
    return files[0]


def verify_data(json_data):
    verify = ""
    if "ipv4_addressing_mode" and "ipv6_addressing_mode" in json_data:
        if json_data["ipv4_addressing_mode"] or json_data["ipv6_addressing_mode"] not in ["static", "dhcp"]:
            verify += f"type {json_data['ipv4_addressing_mode']} and {json_data['ipv6_addressing_mode']} not validate, "
    else:
        verify += f"type missing, "
    if "gateway" in json_data:
        if isinstance(json_data["gateway"], list):
            # => check empty list
            if not json_data["gateway"]:
                # list empty => no gateway
                # reformat outsource json from list to None
                json_data["gateway"] = None
            else:
                verify += "gateway is list -> really outsource?, "
        else:
            if json_data["ip_type"] == 4 and not is_ipv4(json_data["gateway"]):
                verify += "gateway ipv4 not validate, "
            elif json_data["ip_type"] == 6 and not is_ipv6(json_data["gateway"]):
                verify += "gateway ipv6 not validate, "
    if "ipv4_address" in json_data:
        for ip in json_data["ipv4_address"]:
            ip_a = ip.split("/")
            if not is_ipv4(ip_a[0]) or not is_ipv4_subnet(ip_a[1]):
                verify += f"ip_address {ip} ipv4 not validate, "
    if "ipv6_address" in json_data:
        for ip in json_data["ipv6_address"]:
            ip_a = ip.split("/")
            if not is_ipv6(ip_a[0]) or not is_ipv6_subnet(ip_a[1]):
                verify += f"ip_address {ip} ipv6 not validate, "
    return ""


class NetworkConfiguration(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.netplan_config = NetplanConfigManager(prefix=NETWORK_CONFIG_DIR)
        self.logger = c_logger("interface")

    def check_available_interface(self, interfaces_data):
        network_data = self.netplan_config.parse()
        for data in interfaces_data:
            list_bonds = dict_to_list(network_data['network']['bonds'])
            list_bridges = dict_to_list(network_data['network']['bridges'])
            for bond in list_bonds:
                if data in bond[1]["interfaces"]:
                    return False
            for bridge in list_bridges:
                if data in bridge[1]['interfaces']:
                    return False
        return True

    def get_all_interface(self, http_parameters):
        def available_network_interface(dict_interface):
            # get all interface is not config in system
            system_available_interface = get_list_interface()
            not_config_interface = []
            for network_interface in system_available_interface:
                if network_interface not in dict_interface:
                    not_config_interface.append(network_interface)
            return not_config_interface

        # Interface
        dict_interface = self.netplan_config.parse()['network']['ethernets']
        available_interface = available_network_interface(dict_interface)
        list_interface = dict_to_list(dict_interface)
        interface_data = []
        # configured interface
        for item in list_interface:
            interface_data.append(self.read_network_config_detail(item))
        # not configured interface
        for item in available_interface:
            not_config_data = {
                "name": item,
                "ipv4_addressing_mode": None,
                "ipv4_address": None,
                "gateway_ipv4": None,
                "ipv6_addressing_mode": None,
                "ipv6_address": None,
                "gateway_ipv6": None,
                "type": None,
                "dns": None,
                "active": 0,
                "status": 0
            }
            interface_data.append(not_config_data)
        number_of_interface = len(interface_data)
        if 'limit' not in http_parameters:
            http_parameters['limit'] = 10
        if 'offset' not in http_parameters:
            http_parameters['offset'] = 0
        return get_status_code_200(
            reformat_data_with_paging(interface_data, number_of_interface,
                                      http_parameters["limit"], http_parameters["offset"]))

    def get_all_virtual_interface(self, http_parameters, virtual_type):
        return_data_base = []
        # bonds
        if virtual_type == 'bonds':
            dict_data = self.netplan_config.parse()['network']['bonds']
            list_data = dict_to_list(dict_data)
            return_data_base = []
            for bond in list_data:
                return_data_base.append(self.read_network_config_detail(bond))
        # bridges
        elif virtual_type == 'bridges':
            dict_data = self.netplan_config.parse()['network']['bridges']
            list_data = dict_to_list(dict_data)
            return_data_base = []
            for bridge in list_data:
                return_data_base.append(self.read_network_config_detail(bridge))
        number_of_data = len(return_data_base)
        if 'limit' not in http_parameters:
            http_parameters['limit'] = 10
        if 'offset' not in http_parameters:
            http_parameters['offset'] = 0
        return get_status_code_200(
            reformat_data_with_paging(return_data_base, number_of_data,
                                      http_parameters["limit"], http_parameters["offset"]))

    def get_config_detail(self, config_name, config_type):
        network_data = self.netplan_config.parse()["network"][f'{config_type}']
        working_data = dict_to_list(network_data)
        if working_data:
            for data in working_data:
                if data[0] == config_name:
                    return_data = self.read_network_config_detail(data)
                    return status_code_200({}, return_data)
            return status_code_400(f"get.{config_name}.fail.not.exists")
        else:
            return status_code_400(f"get.{config_name}.fail.not.exists")

    def add_new_config_setting(self, json_data, config_type):
        error_code = verify_data(json_data)
        if error_code != "":
            self.logger.log_writer.error(f"Input data error, {error_code}")
            return status_code_400("put.network.fail.client")
        # network_config_backup()
        network_data = self.netplan_config.parse()
        if network_data:
            new_config = parsed_json(json_data)
            check_data = self.get_config_detail(json_data['name'], config_type)
            check = string_to_json(check_data.response[0].decode())['status']
            if check == 400:
                if not self.check_available_interface(new_config['interfaces']):
                    return status_code_400("interface is used")
                network_data["network"][f'{config_type}'].update({f'{json_data["name"]}': new_config})
                network_config = self.netplan_config.update_config(network_data)
                if network_config:
                    write_yaml_file_from_object(get_file_location(), network_config)
                    try:
                        # monitor_setting = log_setting("Network interface", 1, "Edit network interface")
                        network_config_apply()
                        network_config_remove_backup()
                        return status_code_200("put.network.success",
                                               self.read_network_config_detail([json_data['name'], new_config]))
                    except Exception as e:
                        self.logger.log_writer.error(f"Something went wrong, {e}")
                # network_config_rollback()
                self.logger.log_writer.error("Config network fail")
                # monitor_setting = log_setting("Network interface", 0, "Post network failed")
                return status_code_500("put.network.fail.server")
            else:
                # monitor_setting = log_setting("Network interface", 0, "Post network failed, duplicate config")
                return status_code_400("post.network.fail.client")
        else:
            self.logger.log_writer.error(f"Can not add network config {json_data['name']}")
            monitor_setting = log_setting("Network virtual interface", 0, "Post network failed")
            return status_code_400("post.network.fail.client")

    def edit_config_setting(self, config_name, json_data, config_type):
        # error_code = verify_data(json_data)
        # if error_code != "":
        #     self.logger.log_writer.error(f"Input data error, {error_code}")
        #     return status_code_400("put.network.fail.client")
        network_config_backup()
        # get interface name
        network_data = self.netplan_config.parse()
        if network_data:
            new_config_data = parsed_json(json_data)
            network_data["network"][f'{config_type}'][f'{config_name}'].update(new_config_data)
            network_config = self.netplan_config.update_config(network_data)
            if network_config:
                write_yaml_file_from_object(get_file_location(), network_config)
                self.logger.log_writer.debug("Edit network success ")
                try:
                    # monitor_setting = log_setting("Network interface", 1, "Edit network interface")
                    network_config_apply()
                    network_config_remove_backup()
                    return status_code_200("put.network.success",
                                           network_data["network"][f'{config_type}'][f'{config_name}'])
                except Exception as e:
                    self.logger.log_writer.error(f"Something went wrong, {e}")
            network_config_rollback()
            self.logger.log_writer.error("Config network fail")
            monitor_setting = log_setting("Network interface", 0, "Edit network failed")
            return status_code_500("put.network.fail.server")
        else:
            self.logger.log_writer.error(f"Can not get network card {config_name}")
            monitor_setting = log_setting("Network interface", 0, "Edit network failed")
            return status_code_400("put.network.fail.client")

    def read_network_config_detail(self, object):
        def read_static_config(_config):
            ipv4 = []
            ipv6 = []
            for ipaddress in _config['addresses']:
                ip = get_ip_address(ipaddress)
                if is_ipv4(ip):
                    ipv4.append(ipaddress)
                if is_ipv6(ip):
                    ipv6.append(ipaddress)
            gateway_ipv6 = ''
            gateway_ipv4 = ''
            if 'gateway4' in _config or 'gateway6' in _config:
                if ipv4:
                    gateway_ipv4 = _config['gateway4']
                if ipv6:
                    gateway_ipv6 = _config['gateway6']
            return gateway_ipv4, gateway_ipv6, ipv4, ipv6

        ipv4_type = ''
        interface_ipv4_address = []
        _gateway_ipv4_address = ''
        ipv6_type = ''
        interface_ipv6_address = []
        _gateway_ipv6_address = ''
        parameter = ''
        interfaces = ''
        # from now db only to use to map interface with id
        if object[1]:
            config = object[1]
            # check if using dhcp
            if ('dhcp4' in config and config['dhcp4'] != False) or ('dhcp6' in config and config['dhcp6'] != False):
                if 'dhcp4' in config:
                    if config['dhcp4'] is True:
                        ipv4_type = 'dhcp'
                        ipv4_info = read_interface_information(object[0])['ipv4'][0]
                        interface_ipv4_address = [f"{ipv4_info['addr']}/{get_netmask_bits(ipv4_info['netmask'])}"]
                elif 'dhcp6' in config:
                    if config['dhcp6'] is True:
                        ipv6_type = 'dhcp'
                        ipv6_info = read_interface_information(object[0])['ipv6'][0]
                        interface_ipv6_address = [
                            f"{ipv6_info['addr'].split('%')[0]}/{ipv6_info['netmask'].split('/')[1]}"]
            elif 'addresses' in config:
                _gateway_ipv4_address, _gateway_ipv6_address, interface_ipv4_address, interface_ipv6_address \
                    = read_static_config(config)
                if interface_ipv4_address:
                    ipv4_type = 'static'
                if interface_ipv6_address:
                    ipv6_type = 'static'
            else:
                # config of interface not exist
                ipv6_type = None
                ipv4_type = None
                interface_ipv4_address = None
                interface_ipv6_address = None
                gateway_ipv6_address = None
                gateway_ipv4_address = None
            interface_base = {
                "name": object[0],
                "ipv4_addressing_mode": ipv4_type,
                "ipv4_address": interface_ipv4_address,
                "gateway_ipv4": _gateway_ipv4_address,
                "ipv6_addressing_mode": ipv6_type,
                "ipv6_address": interface_ipv6_address,
                "gateway_ipv6": _gateway_ipv6_address,
                "type": "LAN",
                "dns": config['nameservers']['addresses'] if "nameservers" in config else None,
                "active": 1,
                "status": 1
                # "active": 1 if is_interface_operstate_up(object[0]) else 0,
                # "status": 1 if is_interface_operstate_up(object[0]) else 0
            }
            if 'interfaces' in config:
                interfaces = config['interfaces']
                if 'parameters' in config:
                    parameter = config['parameters']['mode']
                    interface_base.update({"parameters": parameter, "interfaces": interfaces})
                else:
                    interface_base.update({"interfaces": interfaces})
            return interface_base
        else:
            self.logger.log_writer.error(f"Query interface error, {object[0]}")
            return {}

    def flush_config_setting(self, config_name, config_type):
        network_config_backup()
        network_config = {}
        network_data = self.netplan_config.parse()
        if network_data:
            check_data = self.get_config_detail(config_name, config_type)
            check = string_to_json(check_data.response[0].decode())['status']
            if check == 200:
                if config_type == 'ethernets':
                    del network_data["network"][f'{config_type}'][f'{config_name}']
                    network_data["network"][f'{config_type}']. \
                        update({f'{config_name}': {'dhcp4': False, 'optional': True}})
                else:
                    del network_data["network"][f'{config_type}'][f'{config_name}']
                write_yaml_file_from_object(get_file_location(), network_data)
                # TODO: remove service
                self.logger.log_writer.debug("Remove config success")
                try:
                    network_config_apply()
                    network_config_remove_backup()
                    return status_code_200("delete.config.success", {})
                except Exception as e:
                    self.logger.log_writer.error(f"Something went wrong, {e}")
            network_config_rollback()
            self.logger.log_writer.error("Delete config fail")
            return status_code_500("delete.config.fail.server")
        else:
            self.logger.log_writer.error(f"Can not get config {config_name}")
            return status_code_400("delete.config.fail.client")
