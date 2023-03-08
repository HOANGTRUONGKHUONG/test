from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .sms_sender_core import SMSSender


class SMSSenderAPI(Resource):
    def __init__(self):
        self.sender = SMSSender()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.sender.get_all_sms_sender(http_parameters)
