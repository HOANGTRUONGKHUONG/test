from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .exception_core import ExceptionConfig



class WAFExceptionAPI(Resource):
    def __init__(self):
        self.exception = ExceptionConfig()

 #   @jwt_required
    def get(self, website_id):
        http_parameters = request.args.to_dict()
        return self.exception.get_all_exception(http_parameters, website_id)


    @jwt_required
    def post(self, website_id):
        json_data = request.get_json()
        return self.exception.add_new_exception(json_data, website_id)

class WAFExceptionDetailAPI(Resource):
    def __init__(self):
        self.exception = ExceptionConfig()

  #  @jwt_required
    def get(self, excep_id, website_id):
        return self.exception.get_exception_detail(excep_id, website_id)
        
    @jwt_required
    def put(self, excep_id, website_id):
        json_data = request.get_json()
        return self.exception.edit_exception(json_data, excep_id, website_id)
        
    @jwt_required
    def delete(self, excep_id, website_id):
        return self.exception.delete_exception(excep_id, website_id)

    