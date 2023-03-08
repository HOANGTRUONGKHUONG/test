from app.functions.monitors.monitor_api import MonitorAPI
from .monitor_bandwidth_ip_core import MonitorBandwidth


class MonitorBandwidthAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorBandwidth)
