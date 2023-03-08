from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import SessionManagerBase, DeadTokenBase
import datetime
from app.functions.login.login_core import Login


class SessionManager(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("session").log_writer
        
    def get_all_session(self, http_parameters):
        list_session_id, number_of_session = get_id_single_table(self.session, self.logger, http_parameters,
                                                                    SessionManagerBase)

        all_session_base_data = []
        all_session_data = []
        try:
            for session in list_session_id:
                self.check_token(session.id)
                all_session_base_data.append(self.read_session_detail(session.id))
                all_session_data = list(filter(None, all_session_base_data))
            self.session.close()
            self.engine_connect.dispose()
            return get_status_code_200(reformat_data_with_paging(
                all_session_data, number_of_session, http_parameters["limit"], http_parameters["offset"]
            ))
        except Exception as e:
            self.logger.error(f"Get all session fail, {e}")
            monitor_setting = log_setting("Session", 0, f"Get all session failed {e}")
            return status_code_500("get.all.session.fail.server")
        
    def logout_session(self, id):
        now = datetime.datetime.now()
        expired = self.session.query(SessionManagerBase).filter(SessionManagerBase.id.__eq__(id)).first()
        try:
            if now < datetime.datetime.fromtimestamp(expired.exp_refresh):
                if now < datetime.datetime.fromtimestamp(expired.exp_access):
                    self.session.query(SessionManagerBase).filter(SessionManagerBase.id.__eq__(id)).delete()
                    refresh_obj = DeadTokenBase(token=expired.jti_access, type="access")
                    self.session.add(refresh_obj)
                    self.session.flush()  
                else:
                    instance = Login()
                    instance.refresh_user_token()
                    self.session.query(SessionManagerBase).filter(SessionManagerBase.id.__eq__(id)).delete()
                    refresh_obj = DeadTokenBase(token=expired.jti_access, type="access")
                    self.session.add(refresh_obj)
                    self.session.flush()
                refresh_obj = DeadTokenBase(token=expired.jti_refresh, type="refresh")
                self.session.add(refresh_obj)
                self.session.flush()       
                try:
                    self.session.commit()
                    
                    monitor_setting = log_setting("Session", 1, "Delete session")
                except Exception as e:
                 #   raise e
                    self.logger.error(f"Delete session fail, {e}")
                    monitor_setting = log_setting("Session", 0, f"Delete session failed {e}")
                    return status_code_500("delete.session.fail.server")
                finally:
                    self.session.close()
                    self.engine_connect.dispose()
                return status_code_200("delete.session.success", {})
        except Exception as e:
        #    raise e
            monitor_setting = log_setting("Session", 0, f"Delet session failed {e}")
            self.logger.error(f"Delete session faile client, {e}")
            return status_code_400("delete.session.fail.client")
        finally:
            self.session.close()

    def read_session_detail(self, session_id):
        session_detail = self.session.query(SessionManagerBase).filter(SessionManagerBase.id.__eq__(session_id)).first()
        if session_detail:
            session_base_data = {
                "id": session_detail.id,
                "ip_address": session_detail.ip_address,
                "login_time": session_detail.login_time,
                "account": session_detail.account
            }
            return session_base_data
        else:
            return {}
        
    
    
    def check_token(self, session_id):
        now = datetime.datetime.now()
        check_expired = self.session.query(SessionManagerBase).filter(SessionManagerBase.id.__eq__(session_id)).first()
        try:
            if now < datetime.datetime.fromtimestamp(check_expired.exp_refresh):
                if now > datetime.datetime.fromtimestamp(check_expired.exp_access):
                    instance = Login()
                    instance.refresh_user_token()
                             
            else:
                self.session.query(SessionManagerBase).filter(SessionManagerBase.id.__eq__(session_id)).delete()
                self.session.commit()
        except Exception as e:
            self.logger.error(f"Token khong thoa man, {e}")
            return status_code_400("get.session.fail.client")
            