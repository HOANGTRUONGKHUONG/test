from app.functions.objects.ip.ip_core import IP
from app.libraries.logger import c_logger
from app.model import IpWhitelistBase


class Whitelist(IP):
    def __init__(self):
        self.logger = c_logger("whitelist")
        super().__init__(self.logger.log_writer, IpWhitelistBase)
