from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from .manager_session_core import SessionManager

class SessionAPI(Resource):
    def __init__(self):
        self.session_manager = SessionManager()
        
    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.session_manager.get_all_session(http_parameters)
    
class SessionDetailAPI(Resource):
    def __init__(self):
        self.session_manager = SessionManager()
  
    @jwt_required
    def delete(self, id):
        return self.session_manager.logout_session(id)