from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .web_scans_vulnerabilities_core import WebScans


class WebScansAPI(Resource):
    def __init__(self):
        self.scans = WebScans()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.scans.get_result(http_parameters)

    @jwt_required
    def post(self):
        scan_json_data = request.get_json()
        return self.scans.create_data_scan(scan_json_data)


class WebScanDetailAPI(Resource):
    def __init__(self):
        self.scans = WebScans()

    @jwt_required
    def delete(self, history_id):
        return self.scans.delete_scan(history_id)

    @jwt_required
    def get(self, history_id):
        return self.scans.get_one_scan(history_id)


class ScanVulnerabilityAPI(Resource):
    def __init__(self):
        self.vulner = WebScans()

    @jwt_required
    def get(self):
        return self.vulner.get_vulnerability()


class LogFile(Resource):
    def __init__(self):
        self.logfile = WebScans()

    @jwt_required
    def get(self):
        return self.logfile.get_list_log_file()


class DownloadLogfile(Resource):
    def __init__(self):
        self.dowload = WebScans()

    @jwt_required
    def get(self, scan_id):
        return self.dowload.download_scanned_file(scan_id)
