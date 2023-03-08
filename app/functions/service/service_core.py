from app.functions.service.service_collections import SERVICE_VALUES
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.firewall import run_config_rule
from app.libraries.data_format.id_helper import get_default_value, get_search_value
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.string_format import string_to_json, json_to_string
from app.libraries.data_format.validate_data import is_port
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import NetworkServiceBase
from app.setting import DEVELOPMENT_ENV


def verify_json_data(json_data):
    verify = ""
    if "port_from" in json_data:
        if not is_port(str(json_data["port_from"])):
            verify += f"port_from {json_data['port_from']} not validate, "
    if "port_to" in json_data:
        if not is_port(str(json_data["port_to"])):
            verify += f"port_to {json_data['port_to']} not validate, "
    if "protocol" in json_data:
        for protocol in json_data["protocol"]:
            if protocol not in SERVICE_VALUES:
                verify += f"protocol {protocol} not validate, "
    return verify


class ServiceConfiguration(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("service").log_writer

    def get_all_service(self, interface_name, http_parameters):
        limit, offset, order = get_default_value(self.logger, http_parameters, NetworkServiceBase)
        list_service_id = self.session.query(NetworkServiceBase.id).filter(
            NetworkServiceBase.interface_name.__eq__(interface_name))
        # search
        list_service_id = get_search_value(http_parameters, self.logger, list_service_id, NetworkServiceBase)
        # group result
        list_service_id = list_service_id.group_by(NetworkServiceBase.id).order_by(order)
        # get final result
        number_of_service = list_service_id.count()
        list_service_id = list_service_id.limit(limit).offset(offset).all()
        # read result
        all_service_base_data = []
        for service in list_service_id:
            all_service_base_data.append(self.read_service_detail(service.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(all_service_base_data, number_of_service, limit, offset))

    def allow_service(self, interface_name, json_data):
        json_error = verify_json_data(json_data)
        if json_error:
            self.logger.error(f"Json data error, {json_error}")
            return status_code_400("post.service.fail.client")
        # TODO: check interface_name is validate
        service_obj = NetworkServiceBase(protocol=json_to_string(json_data["protocol"]),
                                         port_from=json_data["port_from"],
                                         port_to=json_data["port_to"],
                                         interface_name=interface_name)
        self.session.add(service_obj)
        self.session.flush()
        try:
            self.session.commit()
            if DEVELOPMENT_ENV is None:
                status = run_config_rule()
            return status_code_200("post.service.success", self.read_service_detail(service_obj.id))
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Add service fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("post.service.fail.server")

    def get_service_detail(self, service_id):
        service_detail = self.read_service_detail(service_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(service_detail):
            return get_status_code_200(service_detail)
        else:
            return status_code_400("get.service.detail.fail.client")

    def edit_service(self, service_id, json_data):
        service_detail = self.read_service_detail(service_id)
        if not bool(service_detail):
            return status_code_400("put.service.fail.client")

        service_detail.update(json_data)
        service_detail["protocol"] = json_to_string(service_detail["protocol"])
        self.session.query(NetworkServiceBase). \
            filter(NetworkServiceBase.id.__eq__(service_id)).update(service_detail)
        try:
            self.session.commit()
            if DEVELOPMENT_ENV is None:
                status = run_config_rule()
            monitor_setting = log_setting(action="Service", status=1, description="Edit service")
            return status_code_200("put.service.success", self.read_service_detail(service_id))
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Edit service fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        monitor_setting = log_setting(action="Service", status=0, description="Edit service failed")
        return status_code_500("put.service.fail.server")

    def delete_service(self, service_id):
        try:
            self.session.query(NetworkServiceBase).filter(NetworkServiceBase.id.__eq__(service_id)).delete()
        except Exception as e:
            self.logger.error(e)
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("delete.service.fail.client")
        try:
            self.session.commit()
            if DEVELOPMENT_ENV is None:
                status = run_config_rule()
            monitor_setting = log_setting(action="Service", status=1, description="Delete service")
            return status_code_200("delete.service.success", {})
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Delete website fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        monitor_setting = log_setting(action="Service", status=0, description="Delete service failed")
        return status_code_500(f"delete.service.fail.server")

    def read_service_detail(self, service_id):
        service_detail = self.session.query(NetworkServiceBase).filter(NetworkServiceBase.id.__eq__(service_id)).first()
        if service_detail:
            service_base_data = {
                "id": service_detail.id,
                "protocol": string_to_json(service_detail.protocol),
                "port_from": service_detail.port_from,
                "port_to": service_detail.port_to
            }
            return service_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            self.logger.error(f"Query service error {service_detail}")
            return {}
