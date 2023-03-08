from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .mail_sender_core import MailSender


class MailSenderAPI(Resource):
    def __init__(self):
        self.sender = MailSender()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.sender.get_all_mail_sender(http_parameters)

    @jwt_required
    def post(self):
        sender_json_data = request.get_json()
        return self.sender.add_new_mail_sender(sender_json_data)


class MailSenderDetailAPI(Resource):
    def __init__(self):
        self.sender = MailSender()

    @jwt_required
    def get(self, sender_id):
        return self.sender.get_mail_sender_detail(sender_id)

    @jwt_required
    def put(self, sender_id):
        sender_json_data = request.get_json()
        return self.sender.edit_mail_sender(sender_id, sender_json_data)

    @jwt_required
    def delete(self, sender_id):
        return self.sender.delete_mail_sender(sender_id)
