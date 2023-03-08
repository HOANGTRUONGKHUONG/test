from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import UserBase

# def verify_limit(json_data):
#     verify = " "
#     if len(json_data["IP_connection"]) > 100:
#         verify += "IP connection too much, "
#     return verify

class Limit_Conn(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("limit_config").log_writer
        
    def get_limit_conn(self, user_id):
        limit_detail = self.read_limit_conn(user_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(limit_detail):
            return status_code_200("get.limit.conn.success",limit_detail)
        else:
            return status_code_400("get.limit.conn.fail.client")
    
            
    def edit_limit_conn(self, json_data, user_id):
        self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).update({"ip_conn": json_data["IP_connection"]})
        self.session.flush()
        try:
            self.session.commit()
            data = self.read_limit_conn(user_id)
        #    monitor_setting = log_setting("Limit conn", 1, "Edit limit connection")
            return status_code_200("put.limit.connection.success", data)
        except Exception as e:
            self.logger.error(f"Edit limit conn fail, {e}")
     #       monitor_setting = log_setting("Limit conn", 0, "Edit limit connection faild {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.password.fail.server")
        
    def read_limit_conn(self, user_id):
        limit_detail = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        if limit_detail:
            limit_base={
                "IP_connection": limit_detail.ip_conn
            }
            return limit_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}