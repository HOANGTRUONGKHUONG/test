from app.libraries.ORMBase import  ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import status_code_400, status_code_200, status_code_500, get_status_code_200
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import NetworkStaticRouteBase


def verify_route(json_data):
    verify = ""
    return ""


class Route(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("route").log_writer

    def get_all_route(self, http_parameters):
        list_route_id, number_of_route = get_id_single_table(self.session, self.logger, http_parameters,
                                                             NetworkStaticRouteBase)

        all_route_base_data = []
        for route_id in list_route_id:
            all_route_base_data.append(self.read_route_detail(route_id.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_route_base_data, number_of_route, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def add_new_route(self, route_json_data):
        json_error = verify_route(route_json_data)
        if json_error:
            self.logger.error("Json data error,{error}".format(error=json_error))
            return status_code_400("post.route.fail.client")
        route_obj = NetworkStaticRouteBase(name=route_json_data["name"], destination=route_json_data["destination"],
                                           netmask=route_json_data["netmask"], gateway=route_json_data["gateway"],
                                           metric=route_json_data["metric"], interface=route_json_data["interface"],
                                           active=route_json_data["active"], type=route_json_data["type"])
        self.session.add(route_obj)
        self.session.flush()
        try:
            self.session.commit()
            return status_code_200("post.route.success", self.read_route_detail(route_obj.id))
        except Exception as e:
            self.logger.error(f"Add route fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()

        return status_code_500("post.route.fail.server")

    def get_route_detail(self, route_id):
        route_detail = self.read_route_detail(route_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(route_detail):
            return get_status_code_200(route_detail)
        else:
            return status_code_400("get.route.detail.fail.client")

    def edit_route(self, route_id, route_json_data):
        json_error = verify_route(route_json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            return status_code_400("put.route.fail.client")
        route_detail = self.read_route_detail(route_id)
        route_detail.update(route_json_data)
        route_obj = self.session.query(NetworkStaticRouteBase).filter(NetworkStaticRouteBase.id.__eq__(route_id)).one()

        route_obj.name = route_detail["name"]
        route_obj.type = route_detail["type"]
        route_obj.destination = route_detail["destination"]
        route_obj.netmask = route_detail["netmask"]
        route_obj.gateway = route_detail["gateway"]
        route_obj.metric = route_detail["metric"]
        route_obj.interface = route_detail["interface"]
        route_obj.active = route_detail["active"]

        self.session.flush()
        try:
            self.session.commit()
            return status_code_200("put.route.success", self.read_route_detail(route_id))
        except Exception as e:
            self.logger.error(f"Edit route fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.route.fail.server")

    def delete_route(self, route_id):
        try:
            self.session.query(NetworkStaticRouteBase).filter(NetworkStaticRouteBase.id.__eq__(route_id)).delete()
        except Exception as e:
            self.logger.error(e)
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("delete.route.fail.client")
        try:
            self.session.commit()
            monitor_setting = log_setting("Route", 1, "Delete route")
            return status_code_200("delete.route.success", {})
        except Exception as e:
            # self.session.rollback()
            self.logger.error(f"Delete route fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        monitor_setting = log_setting("Route", 0, "Delete route failed")
        return status_code_500(f"delete.route.fail.server")

    def read_route_detail(self, route_id):
        route_detail = self.session.query(NetworkStaticRouteBase). \
            filter(NetworkStaticRouteBase.id.__eq__(route_id)).first()
        if route_detail:
            route_base_data = {
                "id": route_detail.id,
                "name": route_detail.name,
                "destination": route_detail.destination,
                "netmask": route_detail.netmask,
                "gateway": route_detail.gateway,
                "metric": route_detail.metric,
                "interface": route_detail.interface,
                "active": route_detail.active,
                "type": route_detail.type
            }
            return route_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            self.logger.error(f"Query route error {route_detail}")
            return {}
