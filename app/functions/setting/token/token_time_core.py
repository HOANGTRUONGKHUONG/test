from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.configuration.web_server import monitor_restart
from app.libraries.system.log_action import log_setting
import dotenv
import threading
import os


def verify(json_data):
    verify = ""
    # check time
    if int(json_data["access_token_time"]) >= int(json_data["refresh_token_time"]):
        verify += "token time khong thao man, "
    return verify 

class Token(object):
    def __init__(self):
        self.logger = c_logger("toki_config").log_writer
        
    def get_token_time(self):
        list_time = self.read_token_time()
        if bool(list_time):
            return status_code_200("get.token.time.success", list_time)
        else:
            return status_code_400("get.token.time.fail.client")
        
    
    def edit_token_time(self, json_data):
        json_error = verify(json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            return status_code_400("put.access.token.time.fail.client")
        dotenv_file = dotenv.find_dotenv()
        dotenv.load_dotenv(dotenv_file)
        
        os.environ["ACCESS_TOKEN_TIME"] = str(json_data["access_token_time"])
        os.environ["REFRESH_TOKEN_TIME"] = str(json_data["refresh_token_time"]) 
       

        # Write changes to .env file.
        dotenv.set_key(dotenv_file, "ACCESS_TOKEN_TIME", os.environ["ACCESS_TOKEN_TIME"])
        dotenv.set_key(dotenv_file, "REFRESH_TOKEN_TIME", os.environ["REFRESH_TOKEN_TIME"])
        try:
            monitorRestart = threading.Thread(target=monitor_restart, args=())
            monitorRestart.start()
            data = self.read_token_time()
         #   monitor_setting = log_setting("Token time", 1, "Edit token time")
            return status_code_200("put.token.time.success", data)
        except Exception as e:
            self.logger.error(f"Edit token time fail, {e}")
         #   monitor_setting = log_setting("Token time", 0, "Edit token time faild {e}")
        
        return status_code_500("put.token.time.fail.server")
        
        
    def read_token_time(self):
        dotenv_file = dotenv.find_dotenv()
        dotenv.load_dotenv(dotenv_file)
        ACCESS_TOKEN_TIME=os.environ.get("ACCESS_TOKEN_TIME")
        REFRESH_TOKEN_TIME = os.environ.get("REFRESH_TOKEN_TIME")
        token_session = {
            "access_token_time": int(ACCESS_TOKEN_TIME),
            "refresh_token_time": int(REFRESH_TOKEN_TIME)
        }
        return token_session
          