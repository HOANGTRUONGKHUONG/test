from datetime import datetime

import requests

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.string_format import string_to_json
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str, get_current_time
from app.model import LicenceBase

URL = "http://192.168.0.63:8001/device/decode-license"


class Licence(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("licence")

    def read_current_licence(self):
        licence_info = self.read_licence()
        if bool(licence_info):
            return get_status_code_200(licence_info)
        else:
            return status_code_400("System not apply licence")

    def set_system_licence(self, licence_json_data):
        licence_obj = self.session.query(LicenceBase).first()
        if licence_json_data["licence"] == licence_obj.licence:
            return status_code_400("Add.licence.fail.client")
        request_data = {
            "license": licence_json_data["licence"]
        }
        response = requests.post(URL, data=request_data)
        if response.status_code != 200:
            return status_code_400("Add.licence.fail.client")
        response_json = string_to_json(response.text)
        # connect to server check licence valid and date
        expiration_date = datetime.fromtimestamp(response_json['data']['license_detail']['expired_time'])
        server_message = "Licence OK"
        # save to database
        licence_obj.licence = licence_json_data["licence"]
        licence_obj.expiration_date = expiration_date
        self.session.flush()
        try:
            self.session.commit()
            licence_info = self.read_licence()
            licence_info["server_message"] = server_message
            return status_code_200("Licence add success", licence_info)
        except Exception as e:
            self.logger.log_writer.error(f"Add licence fail, {e}")
            return status_code_500("Add licence fail")
        finally:
            self.session.close()
            self.engine_connect.dispose()

    def read_licence(self):
        licence_obj = self.session.query(LicenceBase).first()
        self.session.close()
        self.engine_connect.dispose()
        if licence_obj:
            licence_info = {
                "licence": licence_obj.licence,
                "licence_expired": datetime_to_str(licence_obj.expiration_date)
            }
            return licence_info
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
