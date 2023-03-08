from abc import abstractmethod

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource


class MonitorAPI(Resource):
    @abstractmethod
    def __init__(self, monitor_core):
        self.monitor = monitor_core()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.monitor.get_information(http_parameters)


class MonitorChartAPI(Resource):
    @abstractmethod
    def __init__(self, monitor_core):
        self.monitor = monitor_core()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.monitor.get_monitor_chart(http_parameters)


class MonitorChartCountAPI(Resource):
    def __init__(self, monitor_core):
        self.monitor = monitor_core()

    @jwt_required
    def get(self):
        return self.monitor.get_monitor_count_chart()


class MonitorDownload(Resource):
    def __init__(self, monitor_core):
        self.monitor = monitor_core()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.monitor.download_log(http_parameters)
