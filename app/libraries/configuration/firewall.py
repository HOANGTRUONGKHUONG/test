import datetime
from netaddr import IPAddress

from app.functions.monitors.traffic.monitor_traffic_service import get_list_interface
from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.ORMBase import  ORMSession_alter
from app.libraries.data_format.string_format import string_to_json
from app.libraries.data_format.validate_data import is_ipv4
from app.libraries.system.shell import run_command
from app.libraries.system.sys_time import datetime_to_str, string_to_datetime
from app.model import DDosNetworkLayerBase, IpBlacklistBase, NetworkServiceBase, NetworkInterfaceBase, \
    WebsiteBase, DdosApplicationWebsiteBase, DDosApplicationBase, IpWhitelistBase
from app.model.ClickhouseModel import MonitorDdosApplication
from app.setting import WAF_RULE_DIR, CUSTOM_DEFAULT_INTERFACE


def init_iptables():
    # check if have a env in config -> custom default interface
    if CUSTOM_DEFAULT_INTERFACE is not None:
        default_interface = str(CUSTOM_DEFAULT_INTERFACE)
    else:
        system_network_interface = get_list_interface()
        default_interface = str(system_network_interface[0])
    # allow ssh in default port
    # allow web admin in default port
    run_command(f"iptables -A SERVICE -i {default_interface} -p tcp -m multiport --dports 22,8010 -j ACCEPT")
    run_command(f"ip6tables -A SERVICE -i {default_interface} -p tcp -m multiport --dports 22,8010 -j ACCEPT")


# config Network_DDoS iptables rule
def config_network_rule():
    session,engine_connect = ORMSession_alter()
    list_rule = session.query(DDosNetworkLayerBase).all()
    all_uri_base_data = []
    for uri in list_rule:
        rule_base_data = {
            "id": uri.id,
            "name": uri.name,
            "threshold": uri.threshold,
            "duration": uri.duration,
            "block_duration": uri.block_duration,
            "state": uri.state,
            "alert": uri.alert
        }
        all_uri_base_data.append(rule_base_data)
    config_rule(all_uri_base_data)
    session.close()
    engine_connect.dispose()


def config_rule(array):
    for i in array:
        if i["state"] == 1:
            config_iptables_ddos_rule(i)
        else:
            continue


def config_iptables_ddos_rule(json):
    if json["name"] == "ICMP Flood":
        run_command("iptables -A ICMPFLOOD -m recent --set --name ICMP --rsource ")
        run_command(f"iptables -A ICMPFLOOD -m recent --update --seconds {json['duration']} "
                    f"--hitcount {json['threshold']} --name ICMP --rsource -j LOG "
                    f"--log-prefix 'ICMPFLOOD detected: '  --log-level 4 ")
    elif json["name"] == "UDP Flood":
        run_command("iptables -A UDPFLOOD -m recent --set --name UDP --rsource")
        run_command(f"iptables -A UDPFLOOD -m recent --update --seconds {json['duration']} "
                    f"--hitcount {json['threshold']} --name UDP --rsource -j LOG "
                    f"--log-prefix 'UDPFLOOD detected: '  --log-level 4")
    elif json["name"] == "Syn Flood":
        run_command("iptables -A SYNFLOOD -m recent --set --name SYN --rsource ")
        run_command(f"iptables -A SYNFLOOD -m recent --update --seconds {json['duration']} "
                    f"--hitcount {json['threshold']} --name SYN --rsource -j LOG "
                    f"--log-prefix 'SYNFLOOD detected: '  --log-level 4")
    elif json["name"] == "RST Flood":
        run_command("iptables -A RSTFLOOD -m recent --set --name RST --rsource ")
        run_command(f"iptables -A RSTFLOOD -m recent --update --seconds {json['duration']} "
                    f"--hitcount {json['threshold']} --name RST --rsource -j LOG "
                    f"--log-prefix 'RSTFLOOD detected: '  --log-level 4")


# Config black list iptables rule
def config_rule_blacklist():
    session,engine_connect = ORMSession_alter()
    black_list = session.query(IpBlacklistBase).all()
    all_black_ip_data = []
    for ip in black_list:
        ip_detail = {
            "ip_address": ip.ip_address,
            "ip_subnet": IPAddress(ip.netmask).netmask_bits()
        }
        all_black_ip_data.append(ip_detail)
    session.close()
    engine_connect.dispose()
    for ip in all_black_ip_data:
        if is_ipv4(ip['ip_address']):
            print(run_command(f"iptables -I BLACKLIST -s {ip['ip_address']}/{ip['ip_subnet']} -j DROP"))
        else:
            print(run_command(f"ip6tables -I BLACKLIST -s {ip['ip_address']}/{ip['ip_subnet']} -j DROP"))
    return True


# config service iptables rule
def config_rule_service():
    session,engine_connect = ORMSession_alter()
    list_service_id = session.query(NetworkServiceBase).all()
    init_iptables()
    try:
        for service in list_service_id:
            list_protocol = string_to_json(service.protocol)
            port_from = service.port_from
            port_to = service.port_to
            interface_name = service.interface_name
            if interface_name is not None:
                for protocol in list_protocol:
                    if port_from < port_to:
                        result = run_command(f"iptables -A SERVICE -i {interface_name} -p {protocol} "
                                             f"--match multiport --dports {port_from}:{port_to} -j ACCEPT")
                        result6 = run_command(f"ip6tables -A SERVICE -i {interface_name} -p {protocol} "
                                              f"--match multiport --dports {port_from}:{port_to} -j ACCEPT")
                    elif port_from == port_to:
                        result = run_command(f"iptables -A SERVICE -i {interface_name} -p {protocol} "
                                             f"--match multiport --dports {port_from} -j ACCEPT")
                        result6 = run_command(f"ip6tables -A SERVICE -i {interface_name} -p {protocol} "
                                              f"--match multiport --dports {port_from} -j ACCEPT")
                    else:
                        result = run_command(f"iptables -A SERVICE -i {interface_name} -p {protocol} "
                                             f"--match multiport --dports {port_to}:{port_from} -j ACCEPT")
                        result6 = run_command(f"ip6tables -A SERVICE -i {interface_name} -p {protocol} "
                                              f"--match multiport --dports {port_to}:{port_from} -j ACCEPT")
                    print(result, result6)
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        session.close()
        engine_connect.dispose()


def make_ips_data():
    cdb = ClickhouseBase()
    session,engine_connect = ORMSession_alter()
    websites_under_attack = MonitorDdosApplication.objects_in(cdb).only('website_domain')
    list_ddos_website = []
    list_website = []
    for website in websites_under_attack:
        list_ddos_website.append(website.website_domain)
    for ddos_website in list(set(list_ddos_website)):
        website_id = session.query(WebsiteBase).filter(WebsiteBase.website_domain.__eq__(ddos_website)).first()
        if website_id:
            detail = {
                "id": website_id.id,
                "domain": ddos_website
            }
            list_website.append(detail)
    for website in list_website:
        block_time = []
        list_attack_ip = []
        attack_detail = []
        list_rule_id = session.query(DdosApplicationWebsiteBase, DDosApplicationBase).outerjoin(DDosApplicationBase) \
            .filter(DdosApplicationWebsiteBase.website_id.__eq__(website["id"])).all()
        if list_rule_id:
            for rule_id in list_rule_id:
                block_time. \
                    append(rule_id.DDosApplicationBase.block_time if rule_id.DDosApplicationBase is not None else None)
            website.update({"block_time": max(block_time)})
        attack_ip = MonitorDdosApplication.objects_in(cdb).only('ip_address', 'website_domain'). \
            filter(MonitorDdosApplication.website_domain.__eq__(website["domain"]))
        if attack_ip:
            for ip in attack_ip:
                list_attack_ip.append(ip.ip_address)
        for ip in list(set(list_attack_ip)):
            attack = {}
            details = MonitorDdosApplication.objects_in(cdb). \
                only('ip_address', 'website_domain', 'unlock', 'datetime'). \
                filter(MonitorDdosApplication.ip_address.__eq__(ip),
                       MonitorDdosApplication.website_domain.__eq__(website["domain"])).order_by("datetime")
            for item in details:
                attack = {
                    "unblock_status": item.unlock,
                    "attack_ip": ip,
                    "time_attack": datetime_to_str(item.datetime)
                }
            attack_detail.append(attack)
        website.update({"attack_detail": attack_detail})
    session.close()
    engine_connect.dispose()
    return list_website


def config_rules_whitelist():
    session,engine_connect = ORMSession_alter()
    whitelist = session.query(IpWhitelistBase).all()
    white_ip = []
    white_string = ""
    for ip in whitelist:
        ip_detail = {
            "ip_address": ip.ip_address,
            "ip_subnet": IPAddress(ip.netmask).netmask_bits()
        }
        white_ip.append(ip_detail)
    session.close()
    engine_connect.dispose()
    for ip in white_ip:
        if is_ipv4(ip['ip_address']):
            print(run_command(f"iptables -A WHITELIST -s {ip['ip_address']}/{ip['ip_subnet']} -j SERVICE"))
            white_string = white_string + f"{ip['ip_address']}\n"
        else:
            print(run_command(f"ip6tables -A WHITELIST -s {ip['ip_address']}/{ip['ip_subnet']} -j SERVICE"))
            white_string = white_string + f"{ip['ip_address']}\n"
    f = open(f"{WAF_RULE_DIR}/whitelist.data", "w")
    f.write(white_string)
    f.close()
    return True


def config_rule_ips():
    try:
        for i in make_ips_data():
            for j in i["attack_detail"]:
                if datetime.datetime.now() - string_to_datetime(j["time_attack"]) <= datetime.timedelta(
                        seconds=i["block_time"]):
                    print(add_ip_to_ips_chain(j['attack_ip']))
    except Exception as e:
        print(f"oops, {e}")


def add_ip_to_ips_chain(ip_address):
    if is_ipv4(ip_address):
        try:
            print(f"iptables -A IPS -s {ip_address} -j DROP")
            run_command(f"iptables -A IPS -s {ip_address} -j DROP")
        except Exception as e:
            print(f"Block ip error {e}")
            return False
    else:
        try:
            print(f"ip6tables -A IPS -s {ip_address} -j DROP")
            run_command(f"ip6tables -A IPS -s {ip_address} -j DROP")
        except Exception as e:
            print(f"Block ip error {e}")
            return False
    # done without error -> return True
    return True


def delete_ip_in_ips_chain(ip_address):
    if is_ipv4(ip_address):
        try:
            run_command(f"iptables -D IPS -s {ip_address} -j DROP")
        except Exception as e:
            print(f"Unblock ip error {e}")
            return False
    else:
        try:
            run_command(f"ip6tables -D IPS -s {ip_address} -j DROP")
        except Exception as e:
            print(f"Unblock ip error {e}")
            return False
    # done without error -> return True
    return True


def generate_chain():
    # ipv4
    run_command("iptables -F")
    run_command("iptables -X")
    run_command("iptables -N WHITELIST")
    run_command("iptables -N BLACKLIST")
    run_command("iptables -N ICMPFLOOD")
    run_command("iptables -N UDPFLOOD")
    run_command("iptables -N SYNFLOOD")
    run_command("iptables -N RSTFLOOD")
    run_command("iptables -N IPS")
    run_command("iptables -N SERVICE")
    run_command("iptables -I INPUT -j ACCEPT")
    run_command("iptables -A INPUT -j WHITELIST")
    run_command("iptables -A INPUT -j BLACKLIST")
    run_command("iptables -A INPUT  -p tcp --tcp-flags ALL RST  -m tcp    -j RSTFLOOD ")
    run_command("iptables -A INPUT  -p tcp -m tcp  --syn -m state --state NEW,ESTABLISHED,RELATED,INVALID -j SYNFLOOD ")
    run_command("iptables -A INPUT -p icmp -m icmp --icmp-type 8  -j UDPFLOOD ")
    run_command("iptables -A INPUT -p icmp -m icmp --icmp-type 8  -j ICMPFLOOD ")
    run_command("iptables -A INPUT -j IPS")
    run_command("iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT")
    run_command("iptables -A SERVICE -p icmp --icmp-type echo-request -j ACCEPT")
    run_command("iptables -A INPUT -i lo -j ACCEPT")
    run_command("iptables -A INPUT -j SERVICE")
    run_command("iptables -A INPUT -j DROP")
    # ipv6
    run_command("ip6tables -F")
    run_command("ip6tables -X")
    run_command("ip6tables -N WHITELIST")
    run_command("ip6tables -N BLACKLIST")
    run_command("ip6tables -N IPS")
    run_command("ip6tables -N SERVICE")
    run_command("ip6tables -A INPUT -j WHITELIST")
    run_command("ip6tables -A INPUT -j BLACKLIST")
    run_command("ip6tables -A INPUT -j IPS")
    run_command("ip6tables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT")
    run_command("ip6tables -A SERVICE -p icmp --icmp-type echo-request -j ACCEPT")
    run_command("ip6tables -A INPUT -i lo -j ACCEPT")
    run_command("ip6tables -A INPUT -j SERVICE")
    run_command("ip6tables -A INPUT -j DROP")
    # config rule
    config_rules_whitelist()
    config_rule_blacklist()
    config_network_rule()
    config_rule_ips()
    config_rule_service()


def run_config_rule():
    generate_chain()
