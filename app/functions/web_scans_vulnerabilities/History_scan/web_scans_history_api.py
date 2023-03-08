from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .web_scans_history_core import WebHistory


class WebHistoryAPI(Resource):
    def __init__(self):
        self.history = WebHistory()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.history.get_all_history(http_parameters)


class HistoryInformAPI(Resource):
    def __init__(self):
        self.history = WebHistory()

    @jwt_required
    def get(self, history_id):
        return self.history.get_history_inform(history_id)
