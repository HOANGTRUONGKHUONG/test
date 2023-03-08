from app.functions.log_forward.log_forward_collections import LOG_TYPE_COLLECTIONS
from app.functions.log_forward.syslog.syslog_core import key_in_object, get_list_from_object
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.string_format import json_to_string, string_to_json
from app.libraries.data_format.validate_data import is_ipv4, is_ipv6, is_ipv4_subnet, is_ipv6_subnet, is_port
from app.libraries.http.response import status_code_400, status_code_200, status_code_500, get_status_code_200
from app.libraries.logger import c_logger
from app.libraries.system.snmp_config import snmp_basic_config, snmp_backup, snmp_remove_backup, snmp_apply_config, \
    snmp_rollback, config_snmp, read_snmp_basic_config, check_config_status
from app.model import SNMPCommunityBase


def verify_input(js_data):
    verify = ""
    verify += key_in_object("enable", js_data, [1, 0])
    if "community_name" in js_data:
        if 0 >= len(js_data["community_name"]) >= 255:
            verify += f"{js_data['community_name']} not validate, "
    else:
        verify += "community_name missing, "
    verify += key_in_object("snmp_events", js_data, get_list_from_object(LOG_TYPE_COLLECTIONS))
    if "hosts" in js_data:
        for host in js_data["hosts"]:
            if not is_ipv4(str(host["ip_address"])) and not is_ipv6(str(host["ip_address"])):
                verify += f"{host['ip_address']} not validate, "
            if not is_ipv4_subnet(str(host["netmask"])) and not is_ipv6_subnet(str(host["netmask"])):
                verify += f"{host['netmask']} not validate, "
            verify += key_in_object("accept_queries", host, [1, 0])
            verify += key_in_object("send_traps", host, [1, 0])
    if "queries" in js_data:
        queries = js_data['queries']
        # v1 and v2c
        if "v1_enabled" in queries:
            verify += key_in_object("v1_enabled", queries, [1, 0])
            if not is_port(str(queries['v1_port'])) and queries['v1_enabled'] == 1:
                verify += f"{queries['v1_port']} is not true, "
        if "v2_enabled" in queries:
            verify += key_in_object("v2_enabled", queries, [1, 0])
            if not is_port(str(queries['v2_port'])) and queries['v2_enabled'] == 1:
                verify += f"{queries['v2_port']} is not true, "
        # v3
        if "enabled" in queries:
            verify += key_in_object("enabled", queries, [1, 0])
            if not is_port(str(queries['port'])) and queries['enabled'] == 1:
                verify += f"{queries['port']} is not true, "
    if "traps" in js_data:
        traps = js_data['traps']
        # v1 and v2c
        if "v1_enabled" in traps:
            verify += key_in_object("v1_enabled", traps, [1, 0])
            if not is_port(str(traps['v1_local_port'])) and traps['v1_enabled'] == 1:
                verify += f"{traps['v1_local_port']} is not true, "
            if not is_port(str(traps['v1_remote_port'])) and traps['v1_enabled'] == 1:
                verify += f"{traps['v1_remote_port']} is not true, "
        if "v2_enabled" in traps:
            verify += key_in_object("v2_enabled", traps, [1, 0])
            if not is_port(str(traps['v2_local_port'])) and traps['v2_enabled'] == 1:
                verify += f"{traps['v2_local_port']} is not true, "
            if not is_port(str(traps['v2_remote_port'])) and traps['v2_enabled'] == 1:
                verify += f"{traps['v2_remote_port']} is not true, "
        # v3
        if "enabled" in traps:
            verify += key_in_object("enabled", traps, [1, 0])
            if not is_port(str(traps['local_port'])) and traps['enabled'] == 1:
                verify += f"{traps['local_port']} is not true, "
            if not is_port(str(traps['remote_port'])) and traps['enabled'] == 1:
                verify += f"{traps['remote_port']} is not true, "
    if "security_level" in js_data:
        security_level = js_data["security_level"]
        verify += key_in_object("authentication_algorithm", security_level, ["md5", "sha", None])
        if "authentication_password" in security_level:
            if 0 >= len(security_level["authentication_password"]) >= 255:
                verify += f"{security_level['authentication_password']} not validate, "
        else:
            verify += f"authentication_password missing, "
        verify += key_in_object("private_protocol", security_level, ["des", "aes", None])
        if "private_password" in security_level:
            if 0 >= len(security_level["private_password"]) >= 255:
                verify += f"{security_level['private_password']} not validate, "
        else:
            verify += f"private_password missing, "
    return verify


class SNMPForward(object):
    def __init__(self):
        self.logger = c_logger("snmp_forward")
        self.session, self.engine_connect = ORMSession_alter()

    def read_config(self):
        def reformat_snmp_community(snmp_community_obj):
            community_data = {
                "name": snmp_community_obj["community_name"],
                "hosts": len(snmp_community_obj["hosts"]),
                "events": len(snmp_community_obj["snmp_events"]),
                "status": snmp_community_obj["enable"]
            }
            if snmp_community_obj["version"] == 2:
                community_data["queries"] = {
                    "v1": snmp_community_obj["queries"]["v2_enabled"],
                    "v2": snmp_community_obj["queries"]["v2_enabled"]
                }
                community_data["traps"] = {
                    "v1": snmp_community_obj["traps"]["v2_enabled"],
                    "v2": snmp_community_obj["traps"]["v2_enabled"]
                }
            else:
                community_data["queries"] = snmp_community_obj["queries"]["enabled"]
                community_data["traps"] = snmp_community_obj["traps"]["enabled"]
                community_data["security_level"] = {
                    "authentication": 1
                    if snmp_community_obj["security_level"]["authentication_algorithm"] is not None
                    else 0,
                    "private": 1
                    if snmp_community_obj["security_level"]["private_protocol"] is not None
                    else 0,
                }
            return community_data

        basic_config = read_snmp_basic_config()
        snmp_conf = self.session.query(SNMPCommunityBase).filter(SNMPCommunityBase.community_version.__eq__(2)).all()
        snmp_v3_conf = self.session.query(SNMPCommunityBase).filter(SNMPCommunityBase.community_version.__eq__(3)).all()
        snmp_obj, snmp_v3_obj = [], []
        for item in snmp_conf:
            snmp_obj.append(reformat_snmp_community(self.read_base_item(item)))
        for item in snmp_v3_conf:
            snmp_v3_obj.append(reformat_snmp_community(self.read_base_item(item)))
        snmp_config = {
            "config_status": check_config_status(),
            "description": basic_config["description"],
            "contact_info": basic_config["contact_info"],
            "location": basic_config["location"],
            "snmp": snmp_obj,
            "snmp_v3": snmp_v3_obj
        }
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(snmp_config)

    def snmp_config_info(self, json_data):
        def config_verify_input(js_data):
            verify = ""
            verify += key_in_object("config_status", js_data, [1, 0])
            if "description" in js_data:
                if 0 >= len(js_data["description"]) >= 255:
                    verify += f"{js_data['description']} not validate, "
            else:
                verify += "description missing, "
            if "contact_info" in js_data:
                if 0 >= len(js_data["contact_info"]) >= 255:
                    verify += f"{js_data['contact_info']} not validate, "
            else:
                verify += "contact_info missing, "
            return verify

        json_error = config_verify_input(json_data)
        if json_error != "":
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("post.snmp.fail.client")
        snmp_backup()
        if json_data["config_status"] == 0:
            # remove community in database
            self.session.query(SNMPCommunityBase).delete()
            self.session.flush()
            try:
                self.session.commit()
            except Exception as e:
                self.logger.log_writer.error(e)
        config_success = config_snmp(sys_info=json_data,
                                     community_config=self.read_all_config_to_object(),
                                     enable_status=json_data["config_status"])
        if config_success:
            snmp_apply_config()
            snmp_remove_backup()
            return status_code_200("post.snmp.success", {})
        snmp_rollback()
        self.session.close()
        self.engine_connect.dispose()
        return status_code_500("post.snmp.fail.server")

    def add_snmp_community(self, json_data):
        json_error = verify_input(json_data)
        if json_error != "" or self.is_community_name_exist(json_data["community_name"]):
            self.logger.log_writer.error(f"json data error, {json_error}")
            self.logger.log_writer.error(f"community_name exist {json_data['community_name']}")
            return status_code_400("post.snmp.community.fail.client")

        snmp_backup()
        snmp_community = SNMPCommunityBase(enable=json_data["enable"], community_version=2,
                                           community_name=json_data["community_name"],
                                           community_hosts=json_to_string(json_data["hosts"]),
                                           queries=json_to_string(json_data["queries"]),
                                           traps=json_to_string(json_data["traps"]),
                                           snmp_events=json_to_string(json_data["snmp_events"]))
        self.session.add(snmp_community)
        self.session.flush()
        community_configs = self.read_all_config_to_object()
        config_success = config_snmp(sys_info=read_snmp_basic_config(), community_config=community_configs,
                                     enable_status=1)
        if config_success:
            try:
                self.session.commit()
                snmp_apply_config()
                return status_code_200("post.snmp.community.success", {})
            except Exception as e:
                self.logger.log_writer.error(f"add snmp community fail ,{e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()

        self.session.close()
        self.engine_connect.dispose()
        snmp_rollback()
        return status_code_500("post.snmp.community.fail.server")

    def add_snmp_v3_community(self, json_data):
        json_error = verify_input(json_data)
        if json_error != "" or self.is_community_name_exist(json_data["community_name"]):
            self.logger.log_writer.error(f"json data error, {json_error}")
            self.logger.log_writer.error(f"community_name exist {json_data['community_name']}")
            return status_code_400("post.snmp.community_v3.fail.client")

        snmp_backup()
        snmp_community = SNMPCommunityBase(enable=json_data["enable"], community_version=3,
                                           community_name=json_data["community_name"],
                                           community_hosts=json_to_string(json_data["hosts"]),
                                           security_level=json_to_string(json_data["security_level"]),
                                           queries=json_to_string(json_data["queries"]),
                                           traps=json_to_string(json_data["traps"]),
                                           snmp_events=json_to_string(json_data["snmp_events"]))
        self.session.add(snmp_community)
        self.session.flush()
        community_configs = self.read_all_config_to_object()
        config_success = config_snmp(sys_info=read_snmp_basic_config(), community_config=community_configs,
                                     enable_status=1)
        if config_success:
            try:
                self.session.commit()
                snmp_apply_config()
                return status_code_200("post.snmp.community-v3.success", {})
            except Exception as e:
                self.logger.log_writer.error(f"add snmp_v3 community fail ,{e}")
                snmp_rollback()
            finally:
                self.session.close()
                self.engine_connect.dispose()

        self.session.close()
        self.engine_connect.dispose()
        snmp_rollback()
        return status_code_500("post.snmp.community-v3.fail.server")

    def read_snmp_community_detail(self, community_name):
        return get_status_code_200(self.read_community_detail(community_name=community_name, community_version=2))

    def read_snmp_community_v3_detail(self, community_name):
        return get_status_code_200(self.read_community_detail(community_name=community_name, community_version=3))

    def read_community_detail(self, community_name, community_version):
        community_data = self.session.query(SNMPCommunityBase). \
            filter(SNMPCommunityBase.community_name.__eq__(community_name)
                   and SNMPCommunityBase.community_version.__eq__(community_version)).first()
        return self.read_base_item(community_data)

    def read_base_item(self, base_item):
        if base_item:
            community_detail = {
                "enable": int(base_item.enable),
                "community_name": base_item.community_name,
                "hosts": string_to_json(base_item.community_hosts),
                "queries": string_to_json(base_item.queries),
                "traps": string_to_json(base_item.traps),
                "snmp_events": string_to_json(base_item.snmp_events),
                "version": base_item.community_version
            }
            if base_item.community_version == 3:
                community_detail["security_level"] = string_to_json(base_item.security_level)
            return community_detail
        else:
            return {}

    def is_community_name_exist(self, community_name):
        community_check = self.session.query(SNMPCommunityBase). \
            filter(SNMPCommunityBase.community_name.__eq__(community_name)).first()
        if community_check:
            return True
        return False

    def read_all_config_to_object(self):
        config_community = self.session.query(SNMPCommunityBase).all()
        community_list = []
        for community in config_community:
            community_list.append(self.read_base_item(community))
        return community_list

    def edit_snmp_community(self, community_name, json_data, community_version):
        community_log_str = "community" if community_version == 2 else "community_v3"

        snmp_community_detail = self.session.query(SNMPCommunityBase). \
            filter(SNMPCommunityBase.community_name.__eq__(community_name)
                   and SNMPCommunityBase.community_version == community_version).first()
        if not snmp_community_detail:
            return status_code_400(f"put.snmp.{community_log_str}.fail.client")
        json_error = verify_input(json_data)
        if json_error != "":
            self.logger.log_writer.error(f"{community_name} exist or json_error {json_error}")
            return status_code_400(f"put.snmp.{community_log_str}.fail.client")
        snmp_backup()
        try:
            snmp_community_detail.enable = json_data["enable"]
            snmp_community_detail.community_name = json_data["community_name"]
            snmp_community_detail.community_hosts = json_to_string(json_data["hosts"])
            snmp_community_detail.queries = json_to_string(json_data["queries"])
            snmp_community_detail.traps = json_to_string(json_data["traps"])
            snmp_community_detail.snmp_events = json_to_string(json_data["snmp_events"])
            if community_version == 3:
                snmp_community_detail.security_level = json_to_string(json_data["security_level"])

            self.session.flush()
        except Exception as e:
            self.logger.log_writer.error(e)
            return status_code_500(f"put.snmp.{community_log_str}.fail.server")
        config_success = config_snmp(sys_info=read_snmp_basic_config(),
                                     community_config=self.read_all_config_to_object(),
                                     enable_status=1)
        if config_success:
            try:
                self.session.commit()
                snmp_apply_config()
                return status_code_200(f"put.snmp.{community_log_str}.success", {})
            except Exception as e:
                self.logger.log_writer.error(e)
            finally:
                self.session.close()
                self.engine_connect.dispose()

        self.session.close()
        self.engine_connect.dispose()
        snmp_rollback()
        return status_code_500(f"put.snmp.{community_log_str}.fail.server")

    def edit_snmp_community_detail(self, community_name, json_data):
        return self.edit_snmp_community(community_name, json_data, community_version=2)

    def edit_snmp_community_v3_detail(self, community_name, json_data):
        return self.edit_snmp_community(community_name, json_data, community_version=3)

    def delete_snmp_community(self, community_name):
        try:
            self.session.query(SNMPCommunityBase). \
                filter(SNMPCommunityBase.community_name.__eq__(community_name)).delete()
        except Exception as e:
            self.logger.log_writer.error(e)
            return status_code_400("delete.snmp.community.fail.client")
        snmp_backup()
        self.session.flush()
        community_configs = self.read_all_config_to_object()
        config_success = config_snmp(sys_info=read_snmp_basic_config(), community_config=community_configs,
                                     enable_status=1)
        if config_success:
            try:
                self.session.commit()
                snmp_apply_config()
                return status_code_200("delete.snmp.community.success", {})
            except Exception as e:
                self.logger.log_writer.error(e)
                snmp_rollback()
            finally:
                self.session.close()
                self.engine_connect.dispose()

        self.session.close()
        self.engine_connect.dispose()
        snmp_rollback()
        return status_code_500("delete.snmp.community.fail.server")
