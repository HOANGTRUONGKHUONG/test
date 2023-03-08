from flask import request
#from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource

from .token_time_core import Token


class TokenAPI(Resource):
    def __init__(self):
        self.toki = Token()
  
    def get(self):
        return self.toki.get_token_time()
    
 
    def put(self):
        json_data = request.get_json()
        return self.toki.edit_token_time(json_data)
        