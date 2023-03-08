from abc import ABC, abstractmethod

from netaddr import IPAddress

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.firewall import run_config_rule
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.validate_data import is_ipv4, is_ipv4_subnet, is_ipv6, is_ipv6_subnet
from app.libraries.http.response import get_status_code_200, status_code_500, status_code_200, status_code_400
from app.libraries.system.log_action import log_setting
from app.model import IpWhitelistBase


class IP(ABC):
    @abstractmethod
    def __init__(self, log, ip_base):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = log
        self.ip_base = ip_base
        self.ip_type = 'whitelist' if ip_base == IpWhitelistBase else 'blacklist'

    def verify_input(self, json_data):
        print(self.ip_type)
        netmask = IPAddress(json_data["netmask"]).netmask_bits()
        verify = ""
        # check description
        if "description" in json_data and len(json_data["description"]) > 500:
            verify += "description too long, "

        # check ip and netmask
        if not is_ipv4(json_data["ip_address"]):
            if not is_ipv6(json_data["ip_address"]):
                verify += f"ip {json_data['ip_address']} is not validate, "
            else:
                if is_ipv6_subnet(netmask):
                    verify += f"netmask is not validate, "
        else:
            if not is_ipv4_subnet(netmask):
                verify += f"netmask is not validate, "
        return verify

    def get_list(self, http_parameters):
        list_id, number_of_ip = get_id_single_table(self.session, self.logger, http_parameters, self.ip_base)
        all_ip_base_data = []
        for ip_id in list_id:
            all_ip_base_data.append(self.read_ip_detail(ip_id.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_ip_base_data, number_of_ip, int(http_parameters["limit"]), int(http_parameters["offset"])
            )
        )

    def add_new_ip(self, json_data):
        json_error = self.verify_input(json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            return status_code_400(f"add.new.{self.ip_type}.fail.client")
        list_ip = self.session.query(self.ip_base.ip_address).all()
        current_ips = []
        for ip in list_ip:
            current_ips.append(ip.ip_address)
        if json_data["ip_address"] in current_ips:
            return status_code_400(f"post.ip.to.{self.ip_type}.fail.client.duplicate.ip")
        ip_obj = self.ip_base(ip_address=json_data["ip_address"],
                              netmask=json_data["netmask"], description=json_data["description"])
        self.session.add(ip_obj)
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting(action=f"{self.ip_type}", status=1,
                                          description=f"Add {self.ip_type} ip: "
                                                      f"{json_data['ip_address']}/{json_data['netmask']}")
            data = self.read_ip_detail(ip_obj.id)
        except Exception as e:
            self.logger.error(f"Add black ip fail, {e}")
            monitor_setting = log_setting(action=f"{self.ip_type}", status=0,
                                          description=f"Add {self.ip_type} ip: "
                                                      f"{json_data['ip_address']}/{json_data['netmask']} failed")
            return status_code_500(f"post.ip.to.{self.ip_type}.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        run_config_rule()
        return status_code_200(f"post.ip.to.{self.ip_type}.success", data)

    def get_detail_ip(self, ip_id):
        ip_detail = self.read_ip_detail(ip_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(ip_detail):
            return status_code_200(f"get.ip.{self.ip_type}.success", ip_detail)
        else:
            return status_code_400(f"get.ip.{self.ip_type}.fail.client")

    def edit_ip(self, ip_id, json_data):
        json_error = self.verify_input(json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            return status_code_400(f"edit.new.{self.ip_type}.fail.client")
        ip_detail = self.read_ip_detail(ip_id)
        old_ip, old_netmask = ip_detail['ip_address'], ip_detail['netmask']
        ip_detail.update(json_data)
        ip_obj = self.session.query(self.ip_base).filter(self.ip_base.id.__eq__(ip_id)).one()
        ip_obj.ip_address = ip_detail["ip_address"]
        ip_obj.netmask = ip_detail["netmask"]
        ip_obj.description = ip_detail["description"]
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting(action=f"{self.ip_type}", status=1,
                                          description=f"Edit {self.ip_type} ip: "
                                                      f"{old_ip}/{old_netmask} to "
                                                      f"{ip_detail['ip_address']}/{ip_detail['netmask']}")
            data = self.read_ip_detail(ip_id)
        except Exception as e:
            self.logger.error(f"Edit {self.ip_type} fail, {e}")
            monitor_setting = log_setting(action=f"{self.ip_type}", status=0,
                                          description=f"Edit {self.ip_type}: {old_ip}/{old_netmask} failed")
            return status_code_500(f"put.ip.to.{self.ip_type}.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        run_config_rule()
        return status_code_200(f"put.ip.to.{self.ip_type}.success", data)

    def delete_ip(self, ip_id):
        ip_address = self.read_ip_detail(ip_id)
        self.session.query(self.ip_base).filter(self.ip_base.id.__eq__(ip_id)).delete()
        try:
            self.session.commit()
            monitor_setting = log_setting(action=f"{self.ip_type}", status=1,
                                          description=f"Delete {self.ip_type} ip: "
                                                      f"{ip_address['ip_address']}/{ip_address['netmask']}")
        except Exception as e:
            self.logger.error(f"Delete {self.ip_type} fail, {e}")
            monitor_setting = log_setting(action=f"{self.ip_type}", status=0,
                                          description=f"Delete {self.ip_type} ip: "
                                                      f"{ip_address['ip_address']}/{ip_address['netmask']} failed")
            return status_code_500(f"delete.ip.from.{self.ip_type}.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        run_config_rule()
        return status_code_200(f"delete.ip.from.{self.ip_type}.success", {})

    def read_ip_detail(self, ip_id):
        ip_detail = self.session.query(self.ip_base).filter(self.ip_base.id.__eq__(ip_id)).first()
        self.session.close()
        self.engine_connect.dispose()
        if ip_detail:
            ip_base_data = {
                "id": ip_detail.id,
                "ip_address": ip_detail.ip_address,
                "netmask": ip_detail.netmask,
                "description": ip_detail.description
            }
            return ip_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
