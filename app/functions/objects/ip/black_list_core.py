from app.functions.objects.ip.ip_core import IP
from app.libraries.logger import c_logger
from app.model import IpBlacklistBase


class BlackList(IP):
    def __init__(self):
        self.logger = c_logger("blacklist")
        super().__init__(self.logger.log_writer, IpBlacklistBase)
