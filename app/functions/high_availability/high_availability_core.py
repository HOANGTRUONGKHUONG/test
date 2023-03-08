from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.high_availability import high_availability_config, remove_high_availability_config
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import HighAvailabilityBase
from app.model import HighAvailabilityInterfaceBase
from app.model import HighAvailabilityModeBase
from app.model import NetworkInterfaceBase


class HighAvailability(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("high_availability")

    def get_ha_config(self):
        response_data = self.read_ha_config()
        return get_status_code_200(response_data)

    def create_new_ha(self, ha_json_data):
        ha_config = ha_json_data["config"]
        interface_config = ha_json_data["virtual_interface"]

        ha_config_obj = HighAvailabilityBase(high_availability_mode=ha_config["operation_mode_id"],
                                             device_priority=ha_config["device_priority"],
                                             group_name=ha_config["group_name"],
                                             group_password=ha_config["group_password"],
                                             heartbeat_interface_id=ha_config["heartbeat_interface_id"],
                                             heartbeat_network=ha_config["heartbeat_network"],
                                             heartbeat_netmask=ha_config["heartbeat_netmask"])
        self.session.add(ha_config_obj)
        self.session.flush()
        for interface in interface_config:
            ha_virtual_obj = HighAvailabilityInterfaceBase(id=interface["id"],
                                                           virtual_ip_address=interface["virtual_ip_address"],
                                                           enable=interface["is_enable"],
                                                           priority=interface["priority"])
            self.session.add(ha_virtual_obj)
            self.session.flush()
        config_status = high_availability_config(ha_json_data)
        if config_status:
            try:
                self.session.commit()
                monitor_setting = log_setting(action="High availability", status=1,
                                              description="Add new High availability")
                return status_code_200("high.availability.config.success", self.read_ha_config())
            except Exception as e:
                self.session.rollback()
                monitor_setting = log_setting(action="High availability", status=0,
                                              description="Add new High availability failed")
                self.logger.log_writer.error(f"Add ha fail, {e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        monitor_setting = log_setting(action="High availability", status=0,
                                      description="Add new High availability failed")
        return status_code_500(f"high.availability.config.fail.server")

    def edit_ha_config(self, ha_json_data):
        if self.remove_config_and_database():
            return self.create_new_ha(ha_json_data)
        else:
            return status_code_500("Edit high availability config fail")

    def remove_ha_config(self):
        if self.remove_config_and_database():
            return status_code_200("Remove high availability success", {})
        else:
            return status_code_500("Remove high availability fail")

    def remove_config_and_database(self):
        # delete config
        remove_high_availability_config()
        # delete database
        config_obj_num = self.session.query(HighAvailabilityBase).delete()
        network_obj_num = self.session.query(HighAvailabilityInterfaceBase).delete()
        try:
            self.logger.log_writer.debug(f"Delete config {config_obj_num} items, network {network_obj_num} items")
            self.session.commit()
            monitor_setting = log_setting(action="High availability", status=1,
                                          description="Delete High availability")
            return True
        except Exception as e:
            monitor_setting = log_setting(action="High availability", status=0,
                                          description="Delete High availability failed")
            self.logger.log_writer.error(f"Delete high availability config fail, {e}")
            return False
        finally:
            self.session.close()
            self.engine_connect.dispose()
    def read_ha_config(self):
        config_data = self.read_ha_main_config()
        interface_data = self.read_ha_virtual_interface()
        response_data = {}
        response_data.update(config_data)
        response_data.update(interface_data)
        return response_data

    def read_ha_main_config(self):
        ha_config_obj = self.session.query(HighAvailabilityBase).first()
        ha_config = {
            "high_availability_status": 1 if ha_config_obj else 0,
            "config": {
                "operation_mode_id": ha_config_obj.high_availability_mode if ha_config_obj else None,
                "device_priority": ha_config_obj.device_priority if ha_config_obj else None,
                "group_name": ha_config_obj.group_name if ha_config_obj else None,
                "group_password": ha_config_obj.group_password if ha_config_obj else None,
                "heartbeat_interface_id": ha_config_obj.heartbeat_interface_id if ha_config_obj else None,
                "heartbeat_network": ha_config_obj.heartbeat_network if ha_config_obj else None,
                "heartbeat_netmask": ha_config_obj.heartbeat_netmask if ha_config_obj else None,
            }
        }
        self.session.close()
        self.engine_connect.dispose()
        return ha_config

    def read_ha_virtual_interface(self):
        interface_obj = self.session.query(HighAvailabilityInterfaceBase, NetworkInterfaceBase). \
            outerjoin(NetworkInterfaceBase).all()
        list_virtual_interface = []
        for config in interface_obj:
            data = {
                "id": config.HighAvailabilityInterfaceBase.id,
                "interface_name": config.NetworkInterfaceBase.name,
                "virtual_ip_address": config.HighAvailabilityInterfaceBase.virtual_ip_address,
                "is_enable": config.HighAvailabilityInterfaceBase.enable,
                "priority": config.HighAvailabilityInterfaceBase.priority
            }
            list_virtual_interface.append(data)
        interface_config = {
            "virtual_interface": list_virtual_interface
        }
        self.session.close()
        self.engine_connect.dispose()
        return interface_config

    def list_ha_mode(self):
        list_mode_obj = self.session.query(HighAvailabilityModeBase).all()
        list_mode = []
        for mode in list_mode_obj:
            mode_data = {
                "id": mode.id,
                "mode_name": mode.mode_name
            }
            list_mode.append(mode_data)
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(list_mode)
