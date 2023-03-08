from app.libraries.http.response import get_status_code_200

SERVICE_VALUES = [
    "tcp",
    "udp",
    "icmp"
]


class ServiceCollections(object):
    def __init__(self):
        pass

    def service_access_collections(self):
        return get_status_code_200({
            "protocol": {
                "type": "combo_box",
                "values": SERVICE_VALUES
            }
        })
