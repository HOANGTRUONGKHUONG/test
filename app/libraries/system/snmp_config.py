import os
import shutil
import time

from app.libraries.data_format.validate_data import is_ipv4
from app.libraries.system.shell import run_command
from app.setting import SYSTEM_ETC_DIR

SNMP_BACKUP_DIR = os.path.join("/tmp", "snmp_backup_config")
SNMP_FORWARD_FILE = os.path.join(SYSTEM_ETC_DIR, "snmp", "snmpd.conf")


def config_snmp(sys_info, community_config, enable_status=1):
    snmp_basic_config(enable_status, sys_info)
    port_config = []
    config_string = ""
    for community in community_config:
        if community["version"] == 2:
            port_v1, port_v2 = community["queries"]["v1_port"] if community["queries"]["v1_enabled"] == 1 else None, \
                               community["queries"]["v2_port"] if community["queries"]["v2_enabled"] == 1 else None,
            port_config.extend([port_v1, port_v2])
            config_string += create_community(community)
        else:
            config_string += create_user(community)
            port_v3 = community["queries"]["port"] if community["queries"]["enabled"] == 1 else None
            port_config.append(port_v3)
    port_config = list(set(port_config))
    agent_address_config = agent_address(port_config)
    config_string = agent_address_config + config_string
    with open(SNMP_FORWARD_FILE, "a") as f:
        f.write(config_string)
    return True


def agent_address(agent_addresses=None):
    if agent_addresses is None:
        agent_addresses = []
    config_string = ""
    if len(agent_addresses) > 0:
        for agent in agent_addresses:
            config_string += f"agentaddress udp:{agent}\n"
    return config_string


def create_user(snmp_config):
    community_name = snmp_config["community_name"]
    community_setting = ""
    community_security_level = snmp_config["security_level"]
    security_string = ""
    security_permission = 0  # like linux permission use [0, 1, 3] for authentication level
    if community_security_level["authentication_algorithm"] is not None:
        security_string = f'{str(community_security_level["authentication_algorithm"]).upper()} ' \
                          f'"{community_security_level["authentication_password"]}" '
        security_permission += 1
        if community_security_level["private_protocol"] is not None:
            security_string += f'{str(community_security_level["private_protocol"]).upper()} ' \
                               f'"{community_security_level["private_password"]}"'
            security_permission += 3
    security_level = "noauth"
    if security_permission == 1:
        security_level = "auth"
    if security_permission == 4:
        security_level = "priv"

    community_setting += f"createUser {community_name} {security_string}\n"
    community_setting += f"rouser {community_name} {security_level}\n"
    if snmp_config["enable"] == 1:
        return community_setting
    return None


def create_community(snmp_config):
    community_name = snmp_config["community_name"]
    community_setting = ""
    for community in snmp_config["hosts"]:
        community_ip, community_netmask = community["ip_address"], community["netmask"]
        if is_ipv4(str(community["ip_address"])):
            if community["accept_queries"] == 1:
                community_setting += f"rocommunity {community_name} {community_ip}/{community_netmask}\n"
        else:
            if community["accept_queries"] == 1:
                community_setting += f"rocommunity6 {community_name} {community_ip}/{community_netmask}\n"
    if snmp_config["enable"] == 1:
        return community_setting
    return None


def read_snmp_basic_config():
    basic_config = {
        "description": None,
        "location": None,
        "contact_info": None,
    }
    try:
        with open(SNMP_FORWARD_FILE, "r") as f:
            config = f.readlines()
        for line in config:
            if "sysDescr" in line:
                basic_config["description"] = line.replace("sysDescr", "").rstrip().lstrip()
            if "sysLocation" in line:
                basic_config["location"] = line.replace("sysLocation", "").rstrip().lstrip()
            if "sysContact" in line:
                basic_config["contact_info"] = line.replace("sysContact", "").rstrip().lstrip()
        return basic_config
    except Exception as e:
        print(e)
        return basic_config


def snmp_basic_config(enable_status, sys_info):
    def system_info(name=None, description=None, location=None, contact_info=None):
        sys_info_setting = ""
        if name is not None:
            sys_info_setting += f"sysName {name}\n"
        if description is not None:
            sys_info_setting += f"sysDescr {description}\n"
        if location is not None:
            sys_info_setting += f"sysLocation {location}\n"
        if contact_info is not None:
            sys_info_setting += f"sysContact {contact_info}\n"
        return sys_info_setting

    if int(enable_status) == 1:
        with open(SNMP_FORWARD_FILE, "w") as f:
            f.write(system_info(description=sys_info['description'],
                                location=sys_info['location'], contact_info=sys_info['contact_info']))
    else:
        snmp_config_remove()
    return True


def snmp_config_remove():
    if os.path.exists(SNMP_FORWARD_FILE):
        os.remove(SNMP_FORWARD_FILE)


def snmp_backup():
    if os.path.exists(SNMP_BACKUP_DIR):
        shutil.rmtree(SNMP_BACKUP_DIR)
    shutil.copytree(os.path.join(SYSTEM_ETC_DIR, "snmp"), os.path.join(SNMP_BACKUP_DIR, "snmp"))


def snmp_remove_backup():
    if os.path.exists(SNMP_BACKUP_DIR):
        shutil.rmtree(SNMP_BACKUP_DIR)


def snmp_rollback():
    backup_files = os.path.join(SNMP_BACKUP_DIR, "snmp")
    for file_name in backup_files:
        full_file_name = os.path.join(backup_files, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, os.path.join(SYSTEM_ETC_DIR, "snmp"))


def snmp_apply_config():
    restart_message = run_command("service snmpd stop")
    time.sleep(1)
    restart_message = run_command("service snmp start")
    return True


def check_config_status():
    if os.path.getsize(SNMP_FORWARD_FILE) != 0:
        return 1
    return 0
