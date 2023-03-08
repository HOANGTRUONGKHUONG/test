import os
import datetime

from flask import send_file

from app.functions.backup_restore.backup_schedule_service import backup, FILE_PATH, restore
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.change_data import md5
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.validate_data import *
from app.libraries.http.response import *
from app.libraries.inout.file import get_size
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import BackupScheduleBase, RestoreVersion, UserBase
from app.libraries.data_format.id_helper import get_default_value, get_search_value


DATE_FORMAT = '%Y-%m-%d'


class BackupRestore(object):
    def __init__(self):
        self.logger = c_logger("backup_restore")
        self.session,self.engine_connect = ORMSession_alter()
        try:
            self.list_file = os.listdir(FILE_PATH)
        except Exception:
            os.mkdir(FILE_PATH)

    def restoreNow(self):
        try:
            session,engine_connect = ORMSession_alter()
            return status_code_200("success", {})
        except Exception as exp:
            print (exp)
        finally:
            session.close()
            engine_connect.dispose()

    def upload_backup_file(self, request):
        if "backup_file" in request.files:
            file = request.files['backup_file']
            file.save(f"{FILE_PATH}/{file.filename}")
        log = log_setting("upload file", 1, "upload a file to server")
        return get_status_code_200("Upload file success")

    def backup_now(self, json_data):
        currentTime = datetime.datetime.now()
        try:
            restoreBase = RestoreVersion(
                name = json_data['name'],
                mode = json_data['mode'],
                datetime = currentTime
            )
        except:
            return status_code_400(f"post.backup.fail.server")
        self.session.add(restoreBase)
        self.session.flush()
        try:
            self.session.commit()
            # monitor_setting = log_setting("Backup", 1, "Create a backup")
        except Exception as e:
            self.logger.log_writer.error(f"add backup to database failed {e}")
            monitor_setting = log_setting("Backup", 0, "Create a backup failed")
            return status_code_500(f"post.backup.fail.server")
        return status_code_200("post.backup.success", {})

    def create_backup_file(self, json_data, identity):
        # file_name = ""
        # check = self.session.query(UserBase).filter(UserBase.password.__eq__(md5(json_data["user_password"])),
        #                                             UserBase.user_name.__eq__(identity)).first()
        # if check:
            # today = datetime.datetime.today().strftime(DATE_FORMAT)
            # if json_data["schedule"] == 0:
            #     file_name = file_name + json_data["file_name"] + "+" + identity + "+" + \
            #                 str(today) + "+None" + "+current"
            #     backup(file_name)
            #     monitor_setting = log_setting("backup", 1, "Create a backup current")
            #     return status_cysode_200("post.backup.file.success", {})
            # else:
                currentTime = datetime.datetime.now()
                backup_base = BackupScheduleBase(file_name=json_data["name"], datetime = currentTime,
                                                 start=json_data["day_start"], account=identity,
                                                 period=json_data["period"], mode=json_data["mode"])
                self.session.add(backup_base)
                self.session.flush()
                try:
                    self.session.commit()
                    monitor_setting = log_setting("Backup", 1, "Create a backup schedule")
                except Exception as e:
                    self.logger.log_writer.error(f"add backup schedule to database failed {e}")
                    monitor_setting = log_setting("Backup", 0, "Create a backup failed")
                    return status_code_500(f"post.backup.schedule.fail.server")
                return status_code_200("post.backup.schedule.success", {})
        # else:
        #     monitor_setting = log_setting("Backup", 0, "Create a backup failed")
        #     return status_code_400("post.backup.file.fail.client.password.incorrect")

    def show_backup_file(self, http_parameters):
        try:
            # if "limit" not in http_parameters:
            #     http_parameters['limit'] = 10
            return_data = []
            session,engine_connect = ORMSession_alter()
            # restoreVersions = session.query(RestoreVersion).all()

            list_restore_id, number_of_account = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                RestoreVersion)
            all_account_base_data = []
            for restore in list_restore_id:
                all_account_base_data.append(self.read_restore_version_detail(restore.id))
            self.session.close()
            self.engine_connect.dispose()
            return get_status_code_200(
                reformat_data_with_paging(
                    all_account_base_data, number_of_account, http_parameters["limit"], http_parameters["offset"]
                )
            )

        #     for restoreVersion in restoreVersions:
        #         return_data.append({
        #             'id': restoreVersion.id,
        #             'name': restoreVersion.name,
        #             'mode': restoreVersion.mode,
        #             'description': restoreVersion.description,
        #             'datetime': restoreVersion.datetime
        #         })
        #     # return get_status_code_200({'data': return_data})
        #     return get_status_code_200(
        #         reformat_data_with_paging(
        #             return_data, len(return_data), http_parameters["limit"], http_parameters["offset"]
        #     )
        # )     

        except Exception as e:
            raise  (e)
        finally:
            session.close()
            engine_connect.dispose()
        
    def read_detail_backup_file(self, file_id):
        for i in range(len(self.list_file)):
            if i is int(file_id):
                return_data = {
                    "id": i,
                    "file_name": self.list_file[i].split("+")[0],
                    "file_size": str(get_size(f"{FILE_PATH}/{self.list_file[i]}")) + " bytes",
                    "back_up_time": self.list_file[i].split("+")[2],
                    "account_backup": self.list_file[i].split("+")[1],
                    "backup_type": "current"
                }
                return get_status_code_200(return_data)

    def backup(self, data):
        self.session.add(RestoreVersion(
            name = data['name'],
            mode = data['mode'],
            description = data['description']
        ))
        return status_code_200("success", {}) 

    def restore(self, json_data, file_id, identity):

        check = self.session.query(UserBase).filter(UserBase.password.__eq__(md5(json_data["password"])),
                                                    UserBase.user_name.__eq__(identity)).first()
        if check:
            for i in range(len(self.list_file)):
                if i is int(file_id):
                    restore(self.list_file[i])
                    monitor_setting = log_setting("Restore", 1, "Restore system")
            return status_code_200("restore.backup.file.success", {})
        else:
            monitor_setting = log_setting("Restore", 0, "Restore system failed")
            return status_code_400("post.backup.file.fail.client.password.incorrect")

    def download_backup_file(self, file_id):
        for i in range(len(self.list_file)):
            if i is int(file_id):
                monitor_setting = log_setting("Backup", 1, "Download backup file")
                return send_file(f"{FILE_PATH}/{self.list_file[i]}.zip", mimetype='application/zip',
                                 as_attachment=True, conditional=True)

    def default_setting(self, json_data, identity):
        check = self.session.query(UserBase).filter(UserBase.password.__eq__(md5(json_data["user_password"])),
                                                    UserBase.user_name.__eq__(identity)).first()
        self.session.close()
        self.engine_connect.dispose()
        if check:
            restore(f"{FILE_PATH}/Default_setting")
            monitor_setting = log_setting("restore", 1, "restore default setting")
            return status_code_200("restore.default.success", {})
        else:
            monitor_setting = log_setting("restore", 0, "restore default setting failed")
            return status_code_400("post.backup.file.fail.client.password.incorrect")

    def read_backup_schedule_detail(self, backup_id):
        backup_detai = self.session.query(BackupScheduleBase).filter(BackupScheduleBase.id.__eq__(backup_id)).first()
        self.session.close()
        self.engine_connect.dispose()
        if backup_detai:
            backup_schedule_base = {
                "id": backup_detai.id,
                "name": backup_detai.file_name,
                "datetime": backup_detai.datetime,
                "day_start": backup_detai.start,
                "account": backup_detai.account,
                "period": backup_detai.period,
                "mode": backup_detai.mode
            }
            return backup_schedule_base
        else:
            self.logger.log_writer.error(f"Query BackUp Schedule error, {backup_detai}")
            return {}

    def read_restore_version_detail(self, restore_id):
        restore_detail = self.session.query(RestoreVersion).filter(RestoreVersion.id.__eq__(restore_id)).first()
        self.session.close()
        self.engine_connect.dispose()
        if restore_detail:
            backup_schedule_base = {
                "id": restore_detail.id,
                "name": restore_detail.name,
                "datetime": restore_detail.datetime,
                "description": restore_detail.description,
                "mode": restore_detail.mode
            }
            return backup_schedule_base
        else:
            self.logger.log_writer.error(f"Query Backup Schedule error, {restore_detail}")
            return {}

    def get_all_backup_schedule(self, http_parameters):
        list_backup_id, number_of_account = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                BackupScheduleBase)

        all_account_base_data = []
        for backup_id in list_backup_id:
            all_account_base_data.append(self.read_backup_schedule_detail(backup_id.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_account_base_data, number_of_account, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def check_status(self):
        resp = {
            "status": "0",
            "info": {
                "warning": "There is a restore precess running!",
                "warning_description": "The system will auto restart in ...",
                "progress": "50%",
                "progress_detail": "test data..."
            }
        }
        return status_code_200("get.status.success", resp) 