import json
import socket

from app.libraries.ORMBase import ORMSession_alter
from app.model import HighAvailabilityBase

FILE_CONFIG_IP = "/home/bwaf/bwaf/app/functions/high_availability/ip.conf"


def get_ip():
	while True:
		session, engine_connect = ORMSession_alter()
		ha_data = session.query(HighAvailabilityBase).all()
		udp_data = ""
		for data in ha_data:
			udp_data = data.heartbeat_network
			break
		port = 5010
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.bind(("", port))
		while True:
			received = sock.recvfrom(1024)
			json_received = json.loads(received[0])
			if json_received['signal_packet'] == 'bkav-loadbalancer-ha-signal':
				file = open(FILE_CONFIG_IP, "a+")
				ip_ha = json_received['ip_ha'] + "\n"
				list_ip = file.readlines()
				if ip_ha not in list_ip:
					if str(ip_ha.rstrip()) == str(udp_data.rstrip()):
						print("continue")
						continue
					else:
						file.write(ip_ha)
						print("write")
						# send_ip(ip_ha)
						continue


if __name__ == '__main__':
	get_ip()
