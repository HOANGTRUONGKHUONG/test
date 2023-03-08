from app.libraries.http.response import get_status_code_200


class NetworkCollections(object):
    def __init__(self):
        pass

    def physical_interface_collections(self):
        return get_status_code_200({
            "WAN": {
                "name": "WAN",
                "ipv4_addressing_mode": {
                    "name": "Addressing Mode IPv4",
                    "static": {
                        "name": "Static IPv4",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {}
                    },
                    "dhcp": {
                        "name": "DHCP IPv4",
                        "advanced": {}
                    }
                },
                "ipv6_addressing_mode": {
                    "name": "Addressing Mode IPv6",
                    "static": {
                        "name": "Static IPv6",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {}
                    },
                    "dhcp": {
                        "name": "DHCP IPv6",
                        "advanced": {}
                    }
                }
            },
            "LAN": {
                "name": "LAN",
                "ipv4_addressing_mode": {
                    "name": "Addressing Mode IPv4",
                    "static": {
                        "name": "Static IPv4",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {}
                    },
                    "dhcp": {
                        "name": "DHCP IPv4",
                        "advanced": {}
                    }
                },
                "ipv6_addressing_mode": {
                    "name": "Addressing Mode IPv6",
                    "static": {
                        "name": "Static IPv6",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {}
                    },
                    "dhcp": {
                        "name": "DHCP IPv6",
                        "advanced": {}
                    }
                }
            }
        })

    def virtual_interface_collections(self):
        return get_status_code_200({
            "bonding": {
                "name": "Bonding",
                "interface_name": {
                    "name": "Interface Name",
                    "type": "input"
                },
                "interfaces": {
                    "name": "Interfaces",
                    "type": "input"
                },
                "parameter_mode": {
                    "name": "Parameter Mode",
                    "type": "combo_box",
                    "values": {
                        "balance-rr": {
                            "name": "Balance Round Robin",
                            "advanced": {
                                "monitor-interval": {
                                    "name": "Monitor Interval",
                                    "type": "input"
                                }
                            }
                        },
                        "active-backup": {
                            "name": "Active Backup",
                            "advanced": {
                                "monitor-interval": {
                                    "name": "Monitor Interval",
                                    "type": "input"
                                },
                                "primary_interface": {
                                    "name": "Primary Interface",
                                    "type": "input"
                                }
                            }
                        },
                        "balance-xor": {
                            "name": "Balance XOR",
                            "advanced": {
                                "monitor-interval": {
                                    "name": "Monitor Interval",
                                    "type": "input"
                                }
                            }
                        },
                        "802.3ad": {
                            "name": "802.3ad (LACP)",
                            "advanced": {
                                "monitor-interval": {
                                    "name": "Monitor Interval",
                                    "type": "input"
                                },
                                "lacp-rate": {
                                    "name": "LACP Rate",
                                    "type": "combo_box",
                                    "values": [
                                        "slow",
                                        "fast"
                                    ]
                                }
                            }
                        }
                    }
                },
                "ipv4_addressing_mode": {
                    "name": "Addressing Mode IPv4",
                    "static": {
                        "name": "Static IPv4",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {
                            ""
                        }
                    },
                    "dhcp": {
                        "name": "DHCP IPv4",
                        "advanced": {}
                    }
                },
                "ipv6_addressing_mode": {
                    "name": "Addressing Mode IPv6",
                    "static": {
                        "name": "Static IPv6",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {}
                    },
                    "dhcp": {
                        "name": "DHCP IPv6",
                        "advanced": {}
                    }
                }
            },
            "bridges": {
                "name": "Bridges",
                "interface_name": {
                    "name": "Interface Name",
                    "type": "input"
                },
                "interfaces": {
                    "name": "Interfaces",
                    "type": "input"
                },
                "ipv4_addressing_mode": {
                    "name": "Addressing Mode IPv4",
                    "static": {
                        "name": "Static IPv4",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {}
                    },
                    "dhcp": {
                        "name": "DHCP IPv4",
                        "advanced": {}
                    }
                },
                "ipv6_addressing_mode": {
                    "name": "Addressing Mode IPv6",
                    "static": {
                        "name": "Static IPv6",
                        "addresses": {
                            "name": "Addresses",
                            "type": "input"
                        },
                        "gateway": {
                            "name": "Gateway",
                            "type": "input"
                        },
                        "advanced": {}
                    },
                    "dhcp": {
                        "name": "DHCP IPv6",
                        "advanced": {}
                    }
                }
            }
        })
