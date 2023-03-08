from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .mail_server_core import MailServer


class MailServerAPI(Resource):
    def __init__(self):
        self.server = MailServer()

    @jwt_required
    def get(self):
        return self.server.get_all_mail_server()
