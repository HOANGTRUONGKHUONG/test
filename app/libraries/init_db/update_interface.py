import os
from app.libraries.ORMBase import ORMSession
from app.model import NetworkInterfaceBase

EXCEPT_INTERFACE = ["lo", "docker0"]


class Network(object):
    def __init__(self):
        self.list_network_interface = os.listdir("/sys/class/net")

    def get_interface_mac_address(self, interface_name):
        try:
            with open(f"/sys/class/net/{interface_name}/address") as f:
                mac_address = f.readline().rstrip()
        except Exception as e:
            print(e)
            mac_address = "aa:bb:cc:dd:ee:ff"
        return mac_address

    def main(self):
        print("===== Start update interface =====")
        print(f"Interface found: {self.list_network_interface}")
        list_interface = []
        for network_interface in self.list_network_interface:
            if network_interface not in EXCEPT_INTERFACE:
                mac_address = self.get_interface_mac_address(network_interface)
                print(f"Interface {network_interface}: {mac_address} => Continue")
                list_interface.append(network_interface)
            else:
                print(f"Interface {network_interface} in except interface => Skip")
        # drop old interface
        session = ORMSession()
        interface_db = session.query(NetworkInterfaceBase).all()
        db_interface_list = []
        for item in interface_db:
            db_interface_list.append(item.name)
        print("===== Add interface to database =====")
        # update new interface
        for interface in list_interface:
            if interface not in db_interface_list:
                print(f"Interface {interface} not in database => Continue")
                interface_obj = NetworkInterfaceBase(name=interface)
                session.add(interface_obj)
                session.flush()
            else:
                print(f"Interface {interface} already in database => Skip")
        session.commit()
        session.close()
        print("===== Done =====")


if __name__ == '__main__':
    network = Network()
    network.main()
