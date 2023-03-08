from app.functions.monitors.monitor_api import MonitorAPI
from .monitor_resource_core import MonitorResourceCore


class MonitorResourceAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorResourceCore)
