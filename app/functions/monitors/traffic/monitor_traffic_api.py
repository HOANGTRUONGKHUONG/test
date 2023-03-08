from app.functions.monitors.monitor_api import MonitorAPI
from .monitor_traffic_core import MonitorTraffic


class MonitorTrafficAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorTraffic)
