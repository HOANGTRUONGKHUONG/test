from datetime import datetime

import requests

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.string_format import string_to_json
from app.libraries.http.response import status_code_200, status_code_400
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str
from app.model import LicenceBase

URL_DECODE = "http://192.168.0.63:8001/device/decode-license"
URL_DOWNLOAD = "http://192.168.0.63:8001/device/client-update"



class CheckVersion(object):
	def __init__(self):
		self.session,self.engine_connect = ORMSession_alter()
		self.logger = c_logger("licence")

	def get_lastest_version(self):
		response_json = self.read_licence_data(URL_DECODE)
		version = {
			"version": response_json["data"]['nameVersion'],
			"release_date": datetime_to_str(
				datetime.fromtimestamp(response_json['data']['license_detail']['expired_time'] + 100000))
		}
		return status_code_200("get.update.firmware.check.success", [version])

	def download_version(self):
		response_json = self.read_licence_data(URL_DOWNLOAD)
		version_infor = self.read_licence_data(URL_DECODE)
		if "successfully" in response_json["message"]:
			return_data = {
				"version": version_infor["data"]['nameVersion'],
				"release_date": datetime_to_str(
					datetime.fromtimestamp(version_infor['data']['license_detail']['expired_time']))

			}
			return status_code_200("Dowload Success", return_data)
		else:
			return status_code_400("Download failed")

	def read_licence_data(self, url):
		license_data = self.session.query(LicenceBase).first()
		request_data = {
			"license": license_data.licence
		}
		response = requests.post(url, data=request_data)
		if response.status_code != 200:
			return status_code_400("Something went wrong")
		response_json = string_to_json(response.text)
		self.session.close()
		self.engine_connect.dispose()
		return response_json

	def update_version(self):
		return status_code_200("update version success", [""])
