import copy
import os
import shutil
import netifaces

from app.libraries.data_format.network_calculator import get_netmask_bits
from app.libraries.data_format.string_format import string_to_list
from app.libraries.inout.file import read_yaml_file_to_object, list_all_file_in_folder
from app.libraries.inout.file import write_yaml_file_from_object
from app.libraries.system.available_check import is_interface_operstate_up
from app.libraries.system.shell import run_command
from app.setting import NETWORK_CONFIG_DIR

network_backup_dir = "/tmp/network_backup_config/"
NETWORK_CONFIG_FORM = {
    "network": {
        "version": 2,
        "renderer": "networkd",
        "ethernets": {}
    }
}


def network_config_apply():
    run_command("netplan apply")
    return True


def network_config_remove_backup():
    if os.path.exists(network_backup_dir):
        shutil.rmtree(network_backup_dir)


def network_config_backup():
    network_config_remove_backup()
    shutil.copytree(NETWORK_CONFIG_DIR, network_backup_dir)


def network_config_rollback():
    files = os.listdir(network_backup_dir)
    for f in files:
        shutil.copy(network_backup_dir + f, NETWORK_CONFIG_DIR)


def config_network_interface(interface_id, network_interface, network_conf_object):
    if network_conf_object["ipv4_addressing_mode"] == "static" or \
            network_conf_object["ipv6_addressing_mode"] == "static":
        return config_network_static_interface(interface_id, network_interface, network_conf_object)
    elif network_conf_object["ipv4_addressing_mode"] == "dhcp" or \
            network_conf_object["ipv6_addressing_mode"] == "dhcp":
        return config_network_dhcp_interface(interface_id, network_interface, network_conf_object)
    else:
        return False


def remove_network_interface_config_if_exist(network_interface_id, network_interface_name):
    # check if network interface is config in another file -> remove config in that file and write to new file
    file_config = find_and_read_interface_config_file(network_interface_name)
    remove_status = False
    if file_config["file_name"] is not None:
        print("network config is exist => remove config in that file")
        remove_status = remove_network_config(network_interface_id, network_interface_name)
        print(f"Remove status: {remove_status}")
    else:
        print("network config not exist => create new file")
    return remove_status


def config_network_static_interface(interface_id, network_interface, network_conf_object):
    remove_status = remove_network_interface_config_if_exist(interface_id, network_interface)
    # 00 for config network interface name if need
    # 03 - ... for interface id 1 to ...
    network_interface_id = int(interface_id) + 2
    network_config_file_name = os.path.join(NETWORK_CONFIG_DIR, f"{network_interface_id:02d}-{network_interface}.yaml")
    network_conf = copy.deepcopy(NETWORK_CONFIG_FORM)
    # network_conf["network"]["ethernets"][network_interface] = {
    #     "addresses": network_conf_object["ip_address"]
    # }
    if "dns" in network_conf_object:
        network_conf["network"]["ethernets"][network_interface]["nameservers"] = {
            "addresses": network_conf_object["dns"]
        }
    if network_conf_object["ipv6_addressing_mode"] == "":
        if "gateway" in network_conf_object and network_conf_object["gateway"] is not None:
            network_conf["network"]["ethernets"][network_interface]["gateway4"] = network_conf_object["gateway_ipv4"]
        network_conf["network"]["ethernets"][network_interface] = {
            "addresses": network_conf_object["ipv4_address"]
        }
        write_yaml_file_from_object(network_config_file_name, network_conf)
        return True
    elif network_conf_object["ipv4_addressing_mode"] == "":
        if "gateway" in network_conf_object and network_conf_object["gateway"] is not None:
            network_conf["network"]["ethernets"][network_interface]["gateway6"] = network_conf_object["gateway_ipv6"]
        network_conf["network"]["ethernets"][network_interface] = {
            "addresses": network_conf_object["ipv6_address"]
        }
        write_yaml_file_from_object(network_config_file_name, network_conf)
        return True
    else:
        network_conf["network"]["ethernets"][network_interface]["gateway4"] = network_conf_object["gateway_ipv4"]
        network_conf["network"]["ethernets"][network_interface]["gateway6"] = network_conf_object["gateway_ipv6"]
        write_yaml_file_from_object(network_config_file_name, network_conf)
        return True


def config_network_dhcp_interface(interface_id, network_interface, network_conf_object):
    remove_status = remove_network_interface_config_if_exist(interface_id, network_interface)
    # 00 for config network interface name if need
    # 03 - ... for interface id 1 to ...
    network_interface_id = int(interface_id) + 2
    network_config_file_name = os.path.join(NETWORK_CONFIG_DIR, f"{network_interface_id:02d}-{network_interface}.yaml")
    network_conf = copy.deepcopy(NETWORK_CONFIG_FORM)
    if network_conf_object["ipv4_addressing_mode"] == "dhcp":
        network_conf["network"]["ethernets"][network_interface] = {
            "dhcp4": True
        }
        write_yaml_file_from_object(network_config_file_name, network_conf)
        return True
    elif network_conf_object["ipv6_addressing_mode"] == "dhcp":
        network_conf["network"]["ethernets"][network_interface] = {
            "dhcp6": True
        }
        write_yaml_file_from_object(network_config_file_name, network_conf)
        return True
    else:
        return False


def read_network_interface_config(network_interface=None):
    config_files = list_all_file_in_folder(NETWORK_CONFIG_DIR)
    network_config_all = {'network': {'renderer': 'networkd', 'version': 2, 'ethernets': {}}}
    for file_name in config_files:
        if file_name.endswith(".yaml"):
            network_config_file_name = os.path.join(NETWORK_CONFIG_DIR, file_name)
            network_conf = read_yaml_file_to_object(network_config_file_name)
            network_config_all['network']['ethernets'].update(network_conf['network']['ethernets'])
        else:
            print(f"{file_name} is not yaml extension => skip")
    if network_interface is None:
        return network_config_all
    else:
        network_config = {
            'network': {
                'renderer': 'networkd',
                'version': 2,
                'ethernets': {
                    network_interface: network_config_all['network']['ethernets'][network_interface]
                    if network_interface in network_config_all['network']['ethernets']
                    else {}
                }
            }
        }
        return network_config


def read_system_route_table():
    import socket
    import struct

    def convert_hex_to_ip(hex_ip):
        return socket.inet_ntoa(struct.pack("<L", int(hex_ip, 16)))

    with open("/proc/net/route", "r") as f:
        sys_route = f.readlines()
        # first line is header -> remove first line
        sys_route.pop(0)
    route_table = []
    for route in sys_route:
        route_line = string_to_list(route.rstrip(), '\t')
        route_obj = {
            'iface': route_line[0],
            'destination': convert_hex_to_ip(route_line[1]),
            'gateway': convert_hex_to_ip(route_line[2]),
            'flags': route_line[3],
            'refcnt': route_line[4],
            'use': route_line[5],
            'metric': route_line[6],
            'mask': convert_hex_to_ip(route_line[7]),
            'mtu': route_line[8],
            'window': route_line[8],
            'irtt': route_line[9]
        }
        route_table.append(route_obj)
    return route_table


def find_and_read_interface_config_file(interface_name):
    # config of network interface exist -> find which file
    config_files = list_all_file_in_folder(NETWORK_CONFIG_DIR)
    for file_name in config_files:
        # read file and add route to file if interface in this file
        network_config_file_name = os.path.join(NETWORK_CONFIG_DIR, file_name)
        network_conf = read_yaml_file_to_object(network_config_file_name)
        if interface_name in network_conf['network']['ethernets']:
            return {
                "config": network_conf,
                "file_name": file_name,
                "error": None,
                "status": True,
            }
    return {
        "config": {},
        "file_name": None,
        "error": "config not exist",
        "status": False
    }


def remove_network_config(interface_id, network_interface):
    network_interface_id = int(interface_id) + 2
    network_config_file = os.path.join(NETWORK_CONFIG_DIR, f"{network_interface_id:02d}-{network_interface}.yaml")
    try:
        if os.path.exists(network_config_file):
            # config from web
            os.remove(network_config_file)
        else:
            # config from ssh
            print(f"{network_config_file} not exist => config from ssh")
            file_config = find_and_read_interface_config_file(network_interface)
            if file_config['file_name'] is not None:
                config_file_path = os.path.join(NETWORK_CONFIG_DIR, file_config['file_name'])
                current_file_config_obj = read_yaml_file_to_object(config_file_path)
                del current_file_config_obj['network']['ethernets'][network_interface]
                write_yaml_file_from_object(config_file_path, current_file_config_obj)
            else:
                print("interface is not config")
        return True
    except Exception as e:
        print(e)
        return False


def add_route(route_info):
    # route_info = {
    #     "to": "192.168.100.0",
    #     "netmask": "255.255.255.0",
    #     "gateway": "192.168.1.1",
    #     "interface_name": "eno1"
    # }
    # read all file and file which file is contain interface config -> edit this file and add route
    # check if config exist
    all_config = read_network_interface_config()
    if route_info["interface_name"] in all_config["network"]["ethernets"]:
        # config of network interface exist -> find which file
        file_config = find_and_read_interface_config_file(route_info['interface_name'])
        network_conf = file_config["config"]
        file_name = file_config["file_name"]
        # in python can do this to make code simple, assignment will link the variables
        interface_config = network_conf['network']['ethernets'][route_info["interface_name"]]
        if 'routes' not in interface_config:
            interface_config['routes'] = []
        interface_config['routes'].append(
            {
                "to": f"{route_info['to']}/{get_netmask_bits(route_info['netmask'])}",
                "via": route_info['gateway'],
            }
        )
        network_config_file_name = os.path.join(NETWORK_CONFIG_DIR, file_name)
        write_yaml_file_from_object(network_config_file_name, network_conf)
        return {"status": True, "error": None}
    else:
        # config not exist -> dont add
        return {"status": False, "error": "network interface not exist"}


def delete_route(route_info):
    # route_info = {
    #     "to": "192.168.100.0",
    #     "netmask": "255.255.255.0",
    #     "gateway": "192.168.1.1",
    #     "interface_name": "eno1"
    # }
    all_config = read_network_interface_config()
    if route_info["interface_name"] in all_config["network"]["ethernets"]:
        file_config = find_and_read_interface_config_file(route_info['interface_name'])
        network_conf = file_config["config"]
        file_name = file_config["file_name"]
        # in python can do this to make code simple, assignment will link the variables
        interface_config = network_conf['network']['ethernets'][route_info["interface_name"]]
        if "routes" in interface_config:
            try:
                interface_config["routes"].remove(
                    {
                        "to": f"{route_info['to']}/{get_netmask_bits(route_info['netmask'])}",
                        "via": route_info['gateway'],
                    }
                )
            except ValueError:
                # route not in list -> do nothing
                pass
            network_config_file_name = os.path.join(NETWORK_CONFIG_DIR, file_name)
            # check if route list empty -> remove route from config
            if not interface_config['routes']:
                del interface_config['routes']
            write_yaml_file_from_object(network_config_file_name, network_conf)
            return {
                "status": True,
                "error": None
            }
        else:
            return {
                "status": False,
                "error": "route config not exist"
            }
    else:
        return {"status": False, "error": "network interface not exist"}


def read_interface_information(interface_name):
    net_obj = netifaces.ifaddresses(interface_name)
    return {
        'mac': net_obj[netifaces.AF_LINK],
        'ipv4': net_obj[netifaces.AF_INET],
        'ipv6': net_obj[netifaces.AF_INET6]
    }


def read_system_gateway():
    return netifaces.gateways()


def read_interface_status(interface_name):
    return is_interface_operstate_up(interface_name)
