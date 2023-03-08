from app.functions.monitors.monitor_api import MonitorAPI
from .monitor_http_status_core import MonitorHTTPStatus


class MonitorHTTPStatusAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorHTTPStatus)
