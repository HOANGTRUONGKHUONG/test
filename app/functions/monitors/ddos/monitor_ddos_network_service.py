import re
import time

from app.libraries.logger import c_logger
from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.configuration.firewall import add_ip_to_ips_chain
from app.libraries.location.location_finder import find_country
from app.libraries.system.available_check import check_database_available
from app.libraries.system.shell import run_command
from app.libraries.system.sys_time import get_current_time
from app.model.ClickhouseModel import MonitorDdosNetwork
from app.setting import MONITOR_LOG_DIR

IPTABLES_LOG_FILE_DIR = "/var/log/iptables.log"


def block_ip(ip):
	cdb = ClickhouseBase()
	ips_data = MonitorDdosNetwork.objects_in(cdb).filter(MonitorDdosNetwork.unlock.__eq__(0),
														 MonitorDdosNetwork.ip_address.__eq__(ip))
	if ips_data.count() == 0:
		return add_ip_to_ips_chain(ip)
	else:
		print(f"IP: {ip} already block in db")
		logger.error(f"IP: {ip} already block in db")
		# already have a block in db -> already in iptables -> return False
		return False


def extract_log_information(log_lines):
	list_attacker_obj = {}
	attack_obj = {}
	ATTACK_TYPE = ["ICMPFLOOD", "RSTFLOOD", "SYNFLOOD", "UDPFLOOD"]
	source_regex = re.compile("SRC=([\d.]+)")
	destination_regex = re.compile("DST=([\d.]+)")
	datetime_regex = re.compile("\w+\s\d+\s\d+:\d+:\d+")
	for line in log_lines:
		source_ip = re.search(source_regex, line)
		if source_ip:
			attack_obj = {
				"attacker_ip": f"{(source_ip.group(1))}",
				"country": find_country(source_ip.group(1))
			}
		destination_ip = re.search(destination_regex, line)
		if destination_ip:
			attack_obj.update({"destination_ip": destination_ip.group(1)})
		event_time = re.search(datetime_regex, line)
		if event_time:
			attack_obj.update({"event_time": f"{event_time.group()}"})
		for attack in ATTACK_TYPE:
			if attack in line:
				attack_obj.update({"rule": attack})
		print(attack_obj)
		if attack_obj != {}:
			if attack_obj['attacker_ip'] not in list_attacker_obj:
				list_attacker_obj[attack_obj['attacker_ip']] = attack_obj
			else:
				print("IP already in list")
				pass
		else:
			print("Not a attack event")
			pass
		return list_attacker_obj


def save_event_to_db(event_info):
	cdb = ClickhouseBase()
	detail = run_command(f"cat {IPTABLES_LOG_FILE_DIR} | grep {event_info['attacker_ip']} "
						 f"| grep '{event_info['event_time']}'").decode()
	monitor_ddos_obj = MonitorDdosNetwork(ip_address=event_info["attacker_ip"],
										  attacker_country=event_info["country"],
										  rule=event_info["rule"],
										  unlock=0,
										  detail=detail[:30000])
	try:
		cdb.insert([monitor_ddos_obj])
	except Exception as e:
		pass
		logger.error(f"{e}")
	print("DONE")


def process_log_file(last_size):
	log_file = open(IPTABLES_LOG_FILE_DIR, "r", encoding='utf-8', errors='ignore')
	log_file.seek(0, 2)
	current_size = log_file.tell()
	print(current_size)
	if current_size > last_size:
		logger.debug(f"Detect new log {get_current_time()}")
		print(f"Detect new log {get_current_time()}")
		extend_size = current_size - last_size
		log_file.seek(last_size)
		new_log = log_file.read(extend_size)
		log_lines = new_log.split("\n")
		list_event_obj = extract_log_information(log_lines)
		for ip in list_event_obj:
			if block_ip(ip):
				logger.info(f"Block {ip}")
				save_event_to_db(list_event_obj[ip])
			else:
				logger.error(f"Block ip {ip} fail")
		last_size = current_size
		log_file.close()
		return last_size
	elif current_size < last_size:
		logger.debug("Log rotate -> Reset log")
		last_size = 0
		log_file.close()
		print("Log rotate -> Reset log")
		return last_size
	else:
		log_file.close()
		logger.debug("No new log entry")
		print("No new log entry")
		return current_size


def main():
	print("Monitor DDoS network")
	file = open(IPTABLES_LOG_FILE_DIR, "r")
	file.seek(0, 2)
	last_size = file.tell()
	file.close()
	while True:
		print(last_size)
		last_size = process_log_file(last_size)
		time.sleep(3)


if __name__ == '__main__':
	logger = c_logger(MONITOR_LOG_DIR + "/ddos_network_service.log").log_writer
	while not check_database_available():
		logger.error("Database not available yet")
		time.sleep(1)
	main()
