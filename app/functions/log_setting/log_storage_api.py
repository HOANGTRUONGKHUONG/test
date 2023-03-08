from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from .log_storage_core import LogStorageConfig

class StorageAPI(Resource):
    def __init__(self):
        self.storage = LogStorageConfig()
        
    @jwt_required
    def get(self):
        current_user = get_jwt_identity()
        return self.storage.get_log_storage(current_user)
    
    @jwt_required
    def put(self):
        json_data = request.get_json()
        current_user = get_jwt_identity()
        return self.storage.edit_log_storage(json_data, current_user)