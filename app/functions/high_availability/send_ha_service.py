import json
import time

import requests
import urllib3

from app.libraries.ORMBase import ORMSession_alter
from app.model import HighAvailabilityBase, HighAvailabilityInterfaceBase, NetworkInterfaceBase

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
FILE_CONFIG_IP = "/home/bwaf/bwaf/app/functions/high_availability/ip.conf"
file = open(FILE_CONFIG_IP, "r")
list_ip = file.readlines()
list_url = []
for i in list_ip:
	url = f"https://{i.rstrip()}:8010"
	list_url.append(url)
print(list_url)


def read_ha_virtual_interface():
	session,engine_connect = ORMSession_alter()
	interface_obj = session.query(HighAvailabilityInterfaceBase, NetworkInterfaceBase). \
		outerjoin(NetworkInterfaceBase).all()
	list_virtual_interface = []
	for config in interface_obj:
		data = {
			"id": config.HighAvailabilityInterfaceBase.id,
			"interface_name": config.NetworkInterfaceBase.name,
			"virtual_ip_address": config.HighAvailabilityInterfaceBase.virtual_ip_address,
			"is_enable": config.HighAvailabilityInterfaceBase.enable,
			"priority": config.HighAvailabilityInterfaceBase.priority
		}
		list_virtual_interface.append(data)
	interface_config = {
		"virtual_interface": list_virtual_interface
	}
	session.close()
	engine_connect.dispose()
	return interface_config


def read_ha_config():
	config_data = read_ha_main_config()
	interface_data = read_ha_virtual_interface()
	response_data = {}
	response_data.update(config_data)
	response_data.update(interface_data)
	return response_data


def read_ha_main_config():
	session,engine_connect = ORMSession_alter()
	ha_config_obj = session.query(HighAvailabilityBase).first()
	ha_config = {
		"high_availability_status": 1 if ha_config_obj else 0,
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
	session.close()
	engine_connect.dispose()
	return ha_config


def get_token(user, password):
	return_data = []
	for item in list_url:
		token_url = item + "/ha_api/login_ha"
		json = {
			"user_name": user,
			"password": password
		}
		send_request = requests.post(token_url, json=json, verify=False)
		data = {
			"url": item + "/ha_api/send_ha",
			"access_token": send_request.text.rstrip()
		}
		return_data.append(data)
	return return_data


def send_HA_config():
	while True:
		json_data = read_ha_config()
		list_data = get_token(json_data["config"]["group_name"], json_data["config"]["group_password"])
		print(list_data)
		for data in list_data:
			bearer_token = data['access_token']
			bearer_token = bearer_token.split('"')[1]
			json_data = json.dumps(json_data)
			header = {"User-Agent": "Python API Sample", 'Content-type': 'application/json', 'Accept': 'text/plain',
					  "Authorization": f"Bearer {bearer_token}"}
			send_HA = requests.post(url=data["url"], json=json_data, headers=header, verify=False)
			if send_HA.status_code != 200:
				if send_HA.status_code != 300:
					print(f"Can't send request to {data['url']}")
		time.sleep(10)


if __name__ == '__main__':
	send_HA_config()
