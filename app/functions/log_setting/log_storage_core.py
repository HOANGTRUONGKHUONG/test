from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import get_status_code_200, status_code_200, status_code_400, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import StorageBase


def verify(json_data):
    verify = ""
    if "system_storage_file_size" in json_data and int(json_data["system_storage_file_size"]) >= 2048:
        verify += f"system file qua lon, "
        
    if "waf_storage_file_size" in json_data and int(json_data["waf_storage_file_size"]) >= 2048:
        verify += f"waf file qua lon, "
        
    return verify

class LogStorageConfig(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("log_storage_config").log_writer
        
    def get_log_storage(self, log_storage_id):
        log_storage = self.read_log_storage(log_storage_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(log_storage):
            return get_status_code_200(log_storage)
        else:
            return status_code_400("get.log-storage.fail.client")
        
    
    def edit_log_storage(self, json_data, log_storage_id):
        json_error = verify(json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            return status_code_400("put.storage-log.fail.client")
        log_storage_detail = self.session.query(StorageBase).filter(StorageBase.id.__eq__(log_storage_id)).first()
        if log_storage_detail:
            self.session.query(StorageBase).filter(StorageBase.id.__eq__(log_storage_id)).update({"system_log_time":json_data["system_storage_time"],
                                                                                                    "system_file_size": json_data["system_storage_file_size"],
                                                                                                    "waf_log_time": json_data["waf_storage_time"],
                                                                                                    "waf_file_size": json_data["waf_storage_file_size"]})
        else:
            log_storage_obj = StorageBase(id=log_storage_id, system_log_time=json_data["system_storage_time"], system_file_size=json_data["system_storage_file_size"],
                                          waf_log_time=json_data["waf_storage_time"], waf_file_size=json_data["waf_storage_file_size"])
            self.session.add(log_storage_obj)
            self.session.flush()
        try:
            self.session.commit()
            data = self.read_log_storage(log_storage_id)
            monitor_setting = log_setting("Log storage", 1, "Edit log storage")
            return status_code_200("put.log-storage.success", data)
        except Exception as e:
          #  raise e
            self.logger.error(f"Edit log storage fail, {e}")
            monitor_setting = log_setting("Log storage", 0, "Edit log storage faild {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.log-storage.fail.server")
        
    
    def read_log_storage(self, log_storage_id):
        storage_detail = self.session.query(StorageBase).filter(StorageBase.id.__eq__(log_storage_id)).first()
        if storage_detail:
            storage_base ={
                "system_storage_time": storage_detail.system_log_time,
                "system_storage_file_size": storage_detail.system_file_size,
                "waf_storage_time": storage_detail.waf_log_time,
                "waf_storage_file_size": storage_detail.waf_file_size
            }
            return storage_base
        else:
            return {}
    