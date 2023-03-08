import glob
import logging
import os
import sys
import yaml


class NetplanConfigManager(object):
    def __init__(self, prefix="/", extra_files={}):
        self.prefix = prefix
        self.extra_files = extra_files
        self.config = {}
        self.new_interfaces = set()

    @property
    def network(self):
        return self.config['network']

    @property
    def interfaces(self):
        interfaces = {}
        interfaces.update(self.ovs_ports)
        interfaces.update(self.ethernets)
        interfaces.update(self.modems)
        interfaces.update(self.wifis)
        interfaces.update(self.bridges)
        interfaces.update(self.bonds)
        interfaces.update(self.tunnels)
        interfaces.update(self.vlans)
        return interfaces

    @property
    def physical_interfaces(self):
        interfaces = {}
        interfaces.update(self.ethernets)
        interfaces.update(self.modems)
        interfaces.update(self.wifis)
        return interfaces

    @property
    def ovs_ports(self):
        return self.network['ovs_ports']

    @property
    def openvswitch(self):
        return self.network['openvswitch']

    @property
    def ethernets(self):
        return self.network['ethernets']

    @property
    def modems(self):
        return self.network['modems']

    @property
    def wifis(self):
        return self.network['wifis']

    @property
    def bridges(self):
        return self.network['bridges']

    @property
    def bonds(self):
        return self.network['bonds']

    @property
    def tunnels(self):
        return self.network['tunnels']

    @property
    def vlans(self):
        return self.network['vlans']

    @property
    def nm_devices(self):
        return self.network['nm-devices']

    @property
    def version(self):
        return self.network['version']

    @property
    def renderer(self):
        return self.network['renderer']

    def parse(self, extra_config=[]):
        names_to_paths = {}
        for yaml_dir in ['lib', 'etc', 'run']:
            for yaml_file in glob.glob(os.path.join(self.prefix, yaml_dir, 'netplan', '*.yaml')):
                names_to_paths[os.path.basename(yaml_file)] = yaml_file

        files = [names_to_paths[name] for name in sorted(names_to_paths.keys())]
        self.config['network'] = {
            'version': None,
            'renderer': None,
            'ethernets': {},
            'bridges': {},
            'bonds': {},
            'vlans': {},
            # 'ovs_ports': {},
            # 'openvswitch': {},
            # 'modems': {},
            # 'wifis': {},
            # 'tunnels': {},
            # 'nm-devices': {}
        }
        for yaml_file in files:
            self._merge_yaml_config(yaml_file)
        for yaml_file in extra_config:
            self.new_interfaces |= self._merge_yaml_config(yaml_file)
        return self.config

    def _merge_interface_config(self, orig, new):
        new_interfaces = set()
        changed_ifaces = list(new.keys())

        for ifname in changed_ifaces:
            iface = new.pop(ifname)
            if ifname in orig:
                logging.debug("{} exists in {}".format(ifname, orig))
                orig[ifname].update(iface)
            else:
                logging.debug("{} not found in {}".format(ifname, orig))
                orig[ifname] = iface
                new_interfaces.add(ifname)

        return new_interfaces

    def _merge_yaml_config(self, yaml_file):
        new_interfaces = set()

        try:
            with open(yaml_file) as f:
                yaml_data = yaml.safe_load(f)
                network = None
                if yaml_data is not None:
                    network = yaml_data['network']
                if network:
                    if 'ethernets' in network:
                        new = self._merge_interface_config(self.ethernets, network.get('ethernets'))
                        new_interfaces |= new
                    if 'bridges' in network:
                        new = self._merge_interface_config(self.bridges, network.get('bridges'))
                        new_interfaces |= new
                    if 'bonds' in network:
                        new = self._merge_interface_config(self.bonds, network.get('bonds'))
                        new_interfaces |= new
                    if 'vlans' in network:
                        new = self._merge_interface_config(self.vlans, network.get('vlans'))
                        new_interfaces |= new
                    if 'version' in network:
                        self.network['version'] = network.get('version')
                    if 'renderer' in network:
                        self.network['renderer'] = network.get('renderer')
            return new_interfaces
        except (IOError, yaml.YAMLError):  # pragma: nocover (filesystem failures/invalid YAML)
            logging.error('Error while loading {}, aborting.'.format(yaml_file))
            sys.exit(1)

    def update_config(self, config):
        # config: dict value of config to update, ex: {
        #     'network': {
        #         'ethernets': {
        #             'eno1': {
        #                 'addresses': [
        #                     '10.49.53.49/24'
        #                 ],
        #                 'gateway4': '10.49.53.1',
        #                 'nameservers': {
        #                     'addresses': [
        #                         '1.1.1.1',
        #                         '1.0.0.1'
        #                     ]
        #                 }
        #             }
        #         }
        #     }
        # }
        try:
            with open("/tmp/netplan_tmp.yaml", 'w') as yaml_file:
                yaml.dump(config, yaml_file)
        except Exception as e:
            print(e)
        config_data = self.parse(['/tmp/netplan_tmp.yaml'])
        return config_data

    def delete_config(self, delete_keys):
        # delete_keys: list of keys from outside to inside, ex: ["network", "bonds", "bond-lan"]
        config_data = self.parse()
        config_value = config_data
        index = 0
        for key in delete_keys:
            try:
                if index == len(delete_keys) - 1:
                    del config_value[key]
                else:
                    config_value = config_value[key]
                    index += 1
            except Exception as e:
                print(f"key error {e}")
                return config_data
        return config_data
