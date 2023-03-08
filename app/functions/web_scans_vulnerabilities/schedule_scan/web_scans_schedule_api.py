from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .web_scans_schedule_core import ScanSchedule


class WebScheduleAPI(Resource):
    def __init__(self):
        self.schedule = ScanSchedule()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.schedule.get_all_schedule(http_parameters)

    @jwt_required
    def post(self):
        schedule_json_data = request.get_json()
        return self.schedule.create_schedule(schedule_json_data)


class WebScheduleDetailAPI(Resource):
    def __init__(self):
        self.schedule = ScanSchedule()

    @jwt_required
    def put(self, schedule_id):
        schedule_json_data = request.get_json()
        return self.schedule.edit_schedule(schedule_json_data, schedule_id)

    @jwt_required
    def delete(self, schedule_id):
        return self.schedule.delete_schedule(schedule_id)

    @jwt_required
    def get(self, schedule_id):
        return self.schedule.get_schedule_detail(schedule_id)
