from app.functions.monitors.monitor_api import MonitorAPI
from .monitor_connection_core import MonitorConnection
from .monitor_ip_connection import MonitorIP
from .monitor_web_connection_core import MonitorWebsite


class MonitorConnectionAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorConnection)


class MonitorWebsiteConnectAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorWebsite)


class MonitorIPConnectAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorIP)
