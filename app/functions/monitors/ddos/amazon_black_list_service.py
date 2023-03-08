from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.configuration.aws_waf_config import get_ip_set_data, update_aws_ip_set, add_ip_to_ip_set_data
from app.libraries.data_format.validate_data import is_ipv4, is_ipv6
from app.model.ClickhouseModel import MonitorDdosApplication


def amazon_black_list():
	cdb = ClickhouseBase()
	ip_data = MonitorDdosApplication.objects_in(cdb).only("ip_address", "unlock"). \
		filter(MonitorDdosApplication.unlock.__eq__('0'))
	ipv4_set_data = get_ip_set_data('ipv4')
	ipv4_set_data['list_ip'] = []
	ipv6_set_data = get_ip_set_data('ipv6')
	ipv6_set_data['list_ip'] = []
	for i in ip_data:
		if is_ipv4(i.ip_address):
			ipv4_set_data = add_ip_to_ip_set_data(ipv4_set_data, i.ip_address)
		if is_ipv6(i.ip_address):
			ipv6_set_data = add_ip_to_ip_set_data(ipv6_set_data, i.ip_address)
	try:
		print(update_aws_ip_set(ipv4_set_data, 'ipv4'))
		print(update_aws_ip_set(ipv6_set_data, 'ipv6'))
	except Exception as e:
		print("Noop")
		print(e)


if __name__ == '__main__':
	amazon_black_list()
