import json
import socket
import time

from app.libraries.ORMBase import ORMSession_alter
from app.model import HighAvailabilityBase

FILE_CONFIG_IP = "/home/bwaf/bwaf/app/functions/high_availability/ip.conf"


def send_ip():
	while True:
		session, engine_connect = ORMSession_alter()
		list_udp = []
		ha_data = session.query(HighAvailabilityBase).all()
		udp_data = ""
		for data in ha_data:
			udp_data = data.heartbeat_network
			break
		array_udp_ha = udp_data.split('.')
		udp_base = array_udp_ha[0] + '.' + array_udp_ha[1] + '.' + array_udp_ha[2] + '.'
		json_data = json.dumps({'signal_packet': 'bkav-loadbalancer-ha-signal', 'ip_ha': udp_data})
		port = 5010
		for i in range(0, 255):
			udp_base_format = udp_base + str(i)
			list_udp.append(udp_base_format.rstrip())
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		list_udp.remove(udp_data)
		for i in list_udp:
			sock.sendto(str(json_data).encode(), (i, port))
		print("sendto: " + str(udp_base))
		time.sleep(5)


if __name__ == '__main__':
	send_ip()
