from app.functions.monitors.monitor_api import MonitorAPI, MonitorChartAPI, MonitorChartCountAPI, MonitorDownload
from .monitor_waf_core import MonitorWAF


class MonitorWAFAPI(MonitorAPI):
    def __init__(self):
        super().__init__(MonitorWAF)


class MonitorWAFChartAPI(MonitorChartAPI):
    def __init__(self):
        super().__init__(MonitorWAF)


class MonitorWAFChartCountAPI(MonitorChartCountAPI):
    def __init__(self):
        super().__init__(MonitorWAF)


class MonitorWAFDownload(MonitorDownload):
    def __init__(self):
        super().__init__(MonitorWAF)
