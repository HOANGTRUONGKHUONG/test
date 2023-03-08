from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from app.libraries.system.decore_permission import admin_role_require
from .limit_conn_core import Limit_Conn

class LimitAPI(Resource):
    def __init__(self):
        self.limit = Limit_Conn()
        
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        return self.limit.get_limit_conn(current_user)
    
    @jwt_required
    def put(self):
        current_user = get_jwt_identity()
        json_data = request.get_json()
        return self.limit.edit_limit_conn(json_data, current_user)