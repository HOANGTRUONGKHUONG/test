from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.system.decore_permission import edit_role_require
from app.model import UserBase
from .backup_restore_core import BackupRestore


class RestoreAPI(Resource):
    def __init__(self):
        self.restore = BackupRestore()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.restore.show_backup_file(http_parameters)

    @edit_role_require
    def post(self):
        return self.restore.restoreNow()

class BackupSchedule(Resource):
    def __init__(self):
        self.backup = BackupRestore()

    @jwt_required
    def post(self):
        pass

class RestoreDetailAPI(Resource):
    def __init__(self):
        self.restore = BackupRestore()

    @jwt_required
    def get(self, file_id):
        return self.restore.read_detail_backup_file(file_id)

    @edit_role_require
    def post(self, file_id):
        return self.restore.restoreNow()

class BackupNowAPI(Resource):
    def __init__(self):
        self.backup = BackupRestore()

    @jwt_required
    def post(self):
        json_data = request.get_json()
        return self.backup.backup(json_data)

class BackupNow(Resource):
    def __init__(self):
        self.backup = BackupRestore()
    def post(self):
        json_data = request.get_json()
        return self.backup.backup_now(json_data)

class BackupScheduleAPI(Resource):
    # TODO
    def __init__(self):
        self.backup = BackupRestore()

    @jwt_required
    def get(self):
        http_parameters = request.args.to_dict()
        return self.backup.get_all_backup_schedule(http_parameters)

    @edit_role_require
    def post(self):
        session, engine_connect = ORMSession_alter()
        json_data = request.get_json()
        current_id = get_jwt_identity()
        account = session.query(UserBase).filter(UserBase.id.__eq__(current_id)).first()
        session.close()
        engine_connect.dispose()
        return self.backup.create_backup_file(json_data, account.user_name)


class RestoreDefaultAPI(Resource):
    def __init__(self):
        self.restore = BackupRestore()

    @edit_role_require
    def post(self):
        session, engine_connect = ORMSession_alter()
        current_id = get_jwt_identity()
        account = session.query(UserBase).filter(UserBase.id.__eq__(current_id)).first()
        session.close()
        engine_connect.dispose()
        json_data = request.get_json()
        return self.restore.default_setting(json_data, account.user_name)


class DownloadBackupFile(Resource):
    def __init__(self):
        self.down = BackupRestore()

    @jwt_required
    def get(self, file_id):
        return self.down.download_backup_file(file_id)

class CheckStatus(Resource):
    def __init__(self):
        self.check = BackupRestore()

    @jwt_required
    def get(self):
        return self.check.check_status()