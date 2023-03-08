from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import get_status_code_200
from app.libraries.logger import c_logger
from app.model import MailServerBase


class MailServer(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("object_mail_server")

    def get_all_mail_server(self):
    
        list_server_id = self.session.query(MailServerBase).all()
        print("mai:", list_server_id, type(list_server_id))
        all_server_base_data = []
        for server in list_server_id:
            print("hai: ", server.id)
            all_server_base_data.append(self.read_mail_server_detail(server.id))
    
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(all_server_base_data)

    def read_mail_server_detail(self, server_id):
        server_detail = self.session.query(MailServerBase).filter(MailServerBase.id.__eq__(server_id)).first()
        self.session.close()
        self.engine_connect.dispose()
        if server_detail:
            server_base = {
                "id": server_detail.id,
                "mail_server_name": server_detail.name
            }
            return server_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
