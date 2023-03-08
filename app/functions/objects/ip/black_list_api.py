from .ip_api import IpAPI, IpDetailAPI
from .black_list_core import BlackList


class BlackListAPI(IpAPI):
    def __init__(self):
        super().__init__(BlackList)


class BlackListDetailAPI(IpDetailAPI):
    def __init__(self):
        super().__init__(BlackList)
