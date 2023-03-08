from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .report_core import Report


class ReportAPI(Resource):
    def __init__(self):
        self.report = Report()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.report.get_all_report(http_parameters)

    @jwt_required
    def post(self):
        json_data = request.get_json()
        return self.report.add_new_report(json_data)


class ReportDetailAPI(Resource):
    def __init__(self):
        self.report = Report()

    @jwt_required
    def get(self, report_id):
        return self.report.get_report_detail(report_id)

    @jwt_required
    def put(self, report_id):
        json_data = request.get_json()
        return self.report.edit_report(report_id, json_data)

    @jwt_required
    def delete(self, report_id):
        return self.report.delete_report(report_id)


class PeriodAPI(Resource):
    def __init__(self):
        self.period = Report()

    @jwt_required
    def get(self):
        return self.period.get_period()


class HtmlFormAPI(Resource):
    def __init__(self):
        self.form = Report()

    @jwt_required
    def get(self):
        return self.form.get_html_form()
