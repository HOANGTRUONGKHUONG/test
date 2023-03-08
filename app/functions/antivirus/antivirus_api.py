from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from .antivirus_core import AntivirusCore


class AntivirusAPI(Resource):
    def __init__(self):
        self.host = AntivirusCore()
    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.host.get_all_file_scanned(http_parameters)

class DownloadFileScannedAPI(Resource):
    def __init__(self):
        self.down = AntivirusCore()
    @jwt_required
    def get(self,file_name):
        return self.down.download_file_scanned(file_name)