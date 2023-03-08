from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.model import URIBase, DDosApplicationUriBase


class DDosApplicationUri(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("DDos_Application_Uri")

    def get_all_uri(self, rule_id):
        list_item = self.session.query(DDosApplicationUriBase). \
            filter(DDosApplicationUriBase.ddos_app_id.__eq__(rule_id)).all()
        all_item_base_data = []
        for item in list_item:
            all_item_base_data.append(self.read_uri_detail(item.uri_id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(all_item_base_data)

    def delete_uri(self, uri_id):
        self.session.query(DDosApplicationUriBase). \
            filter(DDosApplicationUriBase.uri_id.__eq__(uri_id)).delete()
        self.session.query(URIBase).filter(URIBase.id.__eq__(uri_id)).delete()
        try:
            self.session.commit()
        except Exception as e:
            self.logger.log_writer.error(f"delete uri fail, {e}")
            return status_code_500(f"delete uri fail")
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("delete uri success", {})

    def read_uri_detail(self, uri_id):
        list_uri_detail = self.session.query(URIBase).filter(
            URIBase.id.__eq__(uri_id)).first()
        if list_uri_detail:
            uri_base_data = {
                "uri_id": list_uri_detail.id,
                "uri": list_uri_detail.uri,
            }
            return uri_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
