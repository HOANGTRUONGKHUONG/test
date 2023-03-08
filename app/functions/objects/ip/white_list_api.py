from .ip_api import IpAPI, IpDetailAPI
from .white_list_core import Whitelist


class WhiteListAPI(IpAPI):
    def __init__(self):
        super().__init__(Whitelist)


class WhiteListDetailAPI(IpDetailAPI):
    def __init__(self):
        super().__init__(Whitelist)
