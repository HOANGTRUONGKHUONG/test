from app.functions.monitors.monitor import Monitor
from app.libraries.logger import c_logger
from app.model import MonitorBandwidthIPBase


class MonitorBandwidth(Monitor):
    def __init__(self):
        log = c_logger("monitor_bandwidth")
        super().__init__(log.log_writer, MonitorBandwidthIPBase)
