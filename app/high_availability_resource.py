import json
import os

from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, create_refresh_token
from flask_restful import Api
from flask_restful import Resource

from app.functions.high_availability.high_availability_core import HighAvailability
from app.libraries.ORMBase import ORMSession
from app.libraries.data_format.change_data import md5
from app.model import HighAvailabilityBase

high_availability_app = Flask(__name__)
CORS(high_availability_app)
sc_key = str(os.urandom(64))
high_availability_app.config['JWT_SECRET_KEY'] = sc_key
jwt = JWTManager(high_availability_app)
# high_availability_app.config['JWT_BLACKLIST_ENABLED'] = True
# high_availability_app.config['PROPAGATE_EXCEPTIONS'] = True
# high_availability_app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
high_availability_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 1800
high_availability_app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 43200
ha_api = Api(high_availability_app)


class LogInHA(Resource):
	def post(self):
		session = ORMSession()
		json_data = request.get_json()
		login_check = session.query(HighAvailabilityBase).filter(
			HighAvailabilityBase.group_name.__eq__(json_data["user_name"]),
			HighAvailabilityBase.group_password.__eq__(json_data["password"])).first()
		session.close()
		if login_check:
			access_token = create_access_token(identity=login_check.group_name)
			# refresh_token = create_refresh_token(identity=login_check.id)
			return access_token
		return False


class HA(Resource):
	@jwt_required
	def post(self):
		session = ORMSession()
		ha_config_obj = session.query(HighAvailabilityBase).first()
		ha_config_data = {
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
		ha_config = HighAvailability()
		json_data = json.loads(request.get_json())
		json_data.update(ha_config_data)
		return ha_config.edit_ha_config(json_data)


ha_api.add_resource(LogInHA, "/ha_api/login_ha", methods=['POST'])
ha_api.add_resource(HA, "/ha_api/send_ha", methods=['POST'])

if __name__ == '__main__':
	high_availability_app.run(host='127.0.0.1', port=7749, debug=True)
