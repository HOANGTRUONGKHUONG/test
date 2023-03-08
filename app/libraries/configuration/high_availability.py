import os

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.network import config_network_static_interface
from app.libraries.data_format.network_calculator import get_netmask_bits, get_ip_address, get_netmask
from app.libraries.system.shell import run_command
from app.model import NetworkInterfaceBase

# TEST_FOLDER MUST BE SET "" WHEN IN PRODUCT
TEST_FOLDER = ""


# TEST_FOLDER = "/mnt/data/Workspace/bwaf/tests"


def high_availability_config(json_data):
    session,engine_connect = ORMSession_alter()
    # config network interface
    heartbeat_interface = json_data['config']
    network_interface_name = session.query(NetworkInterfaceBase.name). \
        filter(NetworkInterfaceBase.id.__eq__(heartbeat_interface["heartbeat_interface_id"])).first()
    heartbeat_interface["heartbeat_interface_name"] = network_interface_name.name
    config_network(heartbeat_interface=heartbeat_interface)
    # config conntrackd
    list_conntrack_ignore = ['127.0.0.1']
    list_network_interface_ip = session.query(NetworkInterfaceBase.ip_address). \
        filter(NetworkInterfaceBase.ip_address.isnot(None)).all()
    for ip in list_network_interface_ip:
        list_conntrack_ignore.append(get_ip_address(ip.ip_address))
    conntrackd_status = config_conntrackd(heartbeat_interface=heartbeat_interface,
                                          conntrack_ignore=list_conntrack_ignore)
    if os.path.exists("/var/lock/conntrack.lock"):
        os.remove("/var/lock/conntrack.lock")
        print("conntrack.lock removed")
    else:
        print("conntrack.lock not exists")
    run_command("service conntrackd restart")
    # config keepalived
    virtual_interface = json_data["virtual_interface"]
    for interface in virtual_interface:
        if interface['is_enable'] == 1:
            virtual_interface_info = session.query(NetworkInterfaceBase.name, NetworkInterfaceBase.ip_address). \
                filter(NetworkInterfaceBase.id.__eq__(interface["id"])).first()
            interface["name"] = virtual_interface_info.name
            interface["netmask"] = heartbeat_interface["heartbeat_netmask"]
    keepalived_status = config_keepalived(heartbeat_interface=heartbeat_interface, virtual_interface=virtual_interface)
    run_command("service keepalived restart")
    session.close()
    engine_connect.dispose()
    return True


def remove_high_availability_config():
    restore_default_keepalived()
    restore_default_conntrackd()
    remove_iptables()
    return True


def restore_default_keepalived():
    run_command("service keepalived stop")
    if os.path.exists(f"{TEST_FOLDER}/etc/keepalived/keepalived.conf"):
        os.remove(f"{TEST_FOLDER}/etc/keepalived/keepalived.conf")
    else:
        print("keepalived config not exists")
    return True


def restore_default_conntrackd():
    run_command("service conntrackd stop")
    if os.path.exists(f"{TEST_FOLDER}/var/lock/conntrack.lock"):
        os.remove(f"{TEST_FOLDER}/var/lock/conntrack.lock")
    else:
        print("conntrack.lock not exists")
    default_value = """# Default debian config. Please, take a look at conntrackd.conf(5)

General {
    HashSize 8192
    HashLimit 65535

    Syslog on

    LockFile /var/lock/conntrackd.lock

    UNIX {
        Path /var/run/conntrackd.sock
        Backlog 20
    }

    SocketBufferSize 262142
    SocketBufferSizeMaxGrown 655355

    # default debian service unit file is of Type=notify
    Systemd on
}

Stats {
    LogFile on
}

"""
    with open(f"{TEST_FOLDER}/etc/conntrackd/conntrackd.conf", "w") as f:
        f.write(default_value)
    return True


def config_iptables(heartbeat_interface_name):
    # Accept any multicast VRRP traffic destined for 224.0.0.0/8 (this is how keepalived communicates).
    run_command("iptables -A High_Availability -d 224.0.0.0/8 -p vrrp -j ACCEPT")
    # Accept any multicast traffic destined for 225.0.0.50 (this is how conntrackd communicates).
    run_command("iptables -A High_Availability -d 225.0.0.50 -j ACCEPT")
    # Accept any traffic on the interface with the direct connection between routers.
    run_command(f"iptables -A High_Availability -i {heartbeat_interface_name} -j ACCEPT")
    return True


def remove_iptables():
    run_command("iptables -F High_Availability")


def config_network(heartbeat_interface):
    network_config_obj = {
        "ip_type": 4,
        "ip_address": f"{heartbeat_interface['heartbeat_network']}/"
                      f"{get_netmask_bits(heartbeat_interface['heartbeat_netmask'])}",
        "gateway": None,
        "dns": ["1.1.1.1", "1.0.0.1"]
    }
    config_network_static_interface(interface_id=heartbeat_interface["heartbeat_interface_id"],
                                    network_interface=heartbeat_interface["heartbeat_interface_name"],
                                    network_conf_object=network_config_obj)


def config_conntrackd(heartbeat_interface, conntrack_ignore):
    iptables_status = config_iptables(heartbeat_interface_name=heartbeat_interface["heartbeat_interface_name"])
    ignore_ip_address = ""
    for ip in conntrack_ignore:
        ignore_ip_address += f"\n\t\t\tIPv4_address {ip}"
    conntrack_config = f"""Sync {{
    Mode FTFW {{
    }}

    Multicast {{
        IPv4_address 225.0.0.50
        Group {heartbeat_interface["group_name"]}
        IPv4_interface {heartbeat_interface["heartbeat_network"]}
        Interface {heartbeat_interface["heartbeat_interface_name"]}
        SndSocketBuffer 1249280
        RcvSocketBuffer 1249280
        Checksum on
    }}
}}

General {{
    Nice -20
    HashSize 32768
    HashLimit 131072
    LogFile on
    LockFile /var/lock/conntrack.lock
    UNIX {{
        Path /var/run/conntrackd.ctl
        Backlog 20
    }}
    NetlinkBufferSize 2097152
    NetlinkBufferSizeMaxGrowth 8388608
    Filter From Userspace {{
        Protocol Accept {{
            TCP
            SCTP
            DCCP
        }}
        Address Ignore {{{ignore_ip_address}
        }}
    }}
}}
"""
    print(conntrack_config)
    with open(f"{TEST_FOLDER}/etc/conntrackd/conntrackd.conf", "w") as f:
        f.write(conntrack_config)
    return True


def config_keepalived(heartbeat_interface, virtual_interface):
    cluster_interface = ""
    for interface in virtual_interface:
        if interface["is_enable"] == 1:
            cluster_interface += f"\n\t\tcluster-{interface['name']}"
        else:
            pass

    vrrp_sync_group_config = f"""vrrp_sync_group router_cluster {{
    group {{{cluster_interface}
    }}
    notify_master "/etc/conntrackd/primary-backup.sh primary"
    notify_backup "/etc/conntrackd/primary-backup.sh backup"
    notify_fault "/etc/conntrackd/primary-backup.sh fault"
}}
"""
    # Operation mode
    vrrp_instance = ""
    if heartbeat_interface["operation_mode_id"] == 1:
        # 1, Active - Active

        pass
    else:
        # 2, Active - Passive
        vrrp_instance = ""
        router_id = 0
        for interface in virtual_interface:
            if interface["is_enable"] == 1:
                vrrp_instance += f"""vrrp_instance cluster-{interface['name']} {{
    interface {interface['name']}
    virtual_router_id {router_id + 50}
    priority {interface['priority']}
    authentication {{
        auth_type AH
        auth_pass {heartbeat_interface['group_password']}
    }} 
    virtual_ipaddress {{
        {interface['virtual_ip_address']}/{interface['netmask']}
    }}
}}
"""
            router_id += 1
        pass
    keep_alive_config = vrrp_sync_group_config + vrrp_instance
    with open(f"{TEST_FOLDER}/etc/keepalived/keepalived.conf", "w") as f:
        f.write(keep_alive_config)
    return True


ha_json_data = {
    "config": {
        "operation_mode_id": 2,
        "device_priority": 230,
        "group_name": "GroupBkav",
        "group_password": "123456",
        "heartbeat_interface_id": 2,
        "heartbeat_network": "10.10.10.1",
        "heartbeat_netmask": "255.255.255.0"
    },
    "virtual_interface": [
        {
            "id": 1,
            "virtual_ip_address": "192.168.0.30",
            "is_enable": 1,
            "priority": 100
        },
        {
            "id": 2,
            "virtual_ip_address": None,
            "is_enable": None,
            "priority": None
        }
    ]
}
