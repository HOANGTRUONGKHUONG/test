from netaddr import IPAddress


def get_netmask_bits(netmask):
    return IPAddress(netmask).netmask_bits()


def get_ip_address(ip_netmask):
    return ip_netmask.split("/")[0]


def get_netmask(ip_netmask):
    return ip_netmask.split("/")[1]
