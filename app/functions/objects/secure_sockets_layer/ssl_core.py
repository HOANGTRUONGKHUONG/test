from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.ssl import ssl_config, remove_ssl
from app.libraries.configuration.web_server import ngx_config_rollback, ngx_config_backup, ngx_config_remove_backup, \
    ngx_reload
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import SSLBase
from OpenSSL import crypto

def verify_json_data(json_data):
    verify = ""
    if "ssl_name" in json_data and len(json_data["ssl_name"]) > 255:
        verify += "name too long, "
    if "ssl_description" in json_data and len(json_data["ssl_description"]) > 255:
        verify += "description too long, "
    # TODO: check verify key cert pair
    # verify ssl pair
    # if "ssl_key" in json_data and "ssl_cert" in json_data:
    #     if not is_validate_ssl_pair(json_data["ssl_key"], json_data["ssl_cert"]):
    #         verify += "ssl key and cert not validate, "
    return verify

def verify_ssl(content_crt,content_key):
    pubkey_crt_obj = crypto.load_certificate(crypto.FILETYPE_PEM, content_crt).get_pubkey()
    pubkey_crt = crypto.dump_publickey(crypto.FILETYPE_PEM,pubkey_crt_obj)
    pubkey_key_obj = crypto.load_privatekey(crypto.FILETYPE_PEM,content_key)
    pubkey_key=crypto.dump_publickey(crypto.FILETYPE_PEM,pubkey_key_obj)
    if pubkey_crt == pubkey_key:
        return True
    else:
        return False

class SSL(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("ssl")

    def get_all_ssl(self, http_parameters):
        list_ssl_id, number_of_ssl = get_id_single_table(self.session, self.logger.log_writer, http_parameters, SSLBase)
        # read result
        all_ssl_base_data = []
        for ssl_id in list_ssl_id:
            ssl_data = self.read_ssl_detail(ssl_id.id)
            all_ssl_base_data.append(ssl_data)
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(all_ssl_base_data, number_of_ssl,
                                      http_parameters["limit"], http_parameters["offset"]))

    def get_ssl_detail(self, ssl_id):
        ssl_detail = self.read_ssl_detail(ssl_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(ssl_detail):
            return get_status_code_200(ssl_detail)
        else:
            return status_code_400("get.ssl.fail.not.exists")

    def create_new_ssl(self, ssl_json_data):
        json_error = verify_json_data(ssl_json_data)
        try:
            if json_error != "":
                self.logger.log_writer.error("Json data error, {error}".format(error=json_error))
                return status_code_400("post.ssl.fail.client")
        except Exception as e:
            return status_code_500(e)
        try:
            if verify_ssl(ssl_json_data["ssl_cert"],ssl_json_data["ssl_key"]) == False:
                return status_code_400("check.your.key.and.crt.file")
        except Exception as e:
            return status_code_500(e)
        ngx_config_backup()
        ssl_obj = SSLBase(ssl_name=ssl_json_data["ssl_name"], ssl_description=ssl_json_data["ssl_description"],
                          ssl_key=ssl_json_data["ssl_key"], ssl_cert=ssl_json_data["ssl_cert"])
        self.session.add(ssl_obj)
        self.session.flush()
        # core
        config_success = ssl_config(ssl_obj.id, ssl_json_data["ssl_key"], ssl_json_data["ssl_cert"])
        if config_success:
            # db
            try:
                self.session.commit()
                monitor_setting = log_setting(action="SSL", status=1, description="Add new SSL")
                ngx_config_remove_backup()
                ngx_reload()
                return status_code_200("post.ssl.success", self.read_ssl_detail(ssl_obj.id))
            except Exception as e:
                monitor_setting = log_setting(action="SSL", status=0, description="Add new SSL failed")
                self.logger.log_writer.error(f"Create ssl pair fail, {e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        ngx_config_rollback()
        return status_code_500("post.ssl.fail.server")

    def edit_ssl(self, ssl_id, ssl_json_data):
        json_error = verify_json_data(ssl_json_data)
        try:
            if json_error != "":
                self.logger.log_writer.error("Json data error, {error}".format(error=json_error))
                return status_code_400("put.ssl.fail.client")
        except Exception as e:
            return status_code_500(e)
        try:
            if verify_ssl(ssl_json_data["ssl_cert"],ssl_json_data["ssl_key"]) == False:
                return status_code_400("check.your.key.and.crt.file")
        except Exception as e:
            return status_code_500(e)
        ngx_config_backup()
        ssl_detail = self.read_ssl_detail(ssl_id)
        ssl_detail.update(ssl_json_data)
        # core
        config_success = ssl_config(ssl_id, ssl_detail["ssl_key"], ssl_detail["ssl_cert"])
        if config_success:
            # db
            ssl_obj = self.session.query(SSLBase).filter(SSLBase.id.__eq__(ssl_id)).one()
            ssl_obj.ssl_name = ssl_detail["ssl_name"]
            ssl_obj.ssl_description = ssl_detail["ssl_description"]
            ssl_obj.ssl_key = ssl_detail["ssl_key"]
            ssl_obj.ssl_cert = ssl_detail["ssl_cert"]
            self.session.flush()
            try:
                self.session.commit()
                monitor_setting = log_setting(action="SSL", status=1, description="Edit SSL")
                ngx_config_remove_backup()
                ngx_reload()
                return status_code_200("put.ssl.success", self.read_ssl_detail(ssl_id))
            except Exception as e:
                self.logger.log_writer.error(f"Edit ssl error, {e}")
                monitor_setting = log_setting(action="SSL", status=0, description="Edit SSL failed")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        ngx_config_rollback()
        return status_code_500("put.ssl.fail.server")

    def delete_ssl(self, ssl_id):
        ngx_config_backup()
        try:
            # try delete to know if ssl pair is using for any object website
            self.session.query(SSLBase).filter(SSLBase.id.__eq__(ssl_id)).delete()
        except Exception as e:
            self.logger.log_writer.error(e)
            return status_code_400("delete.ssl.fail.client")
        # core
        remove_success = remove_ssl(ssl_id)
        if remove_success:
            # db
            try:
                self.session.commit()
                ngx_config_remove_backup()
                ngx_reload()
                monitor_setting = log_setting(action="SSL", status=1, description="Delete SSL")
                return status_code_200("delete.ssl.success", {})
            except Exception as e:
                monitor_setting = log_setting(action="SSL", status=0, description="Delete SSL failed")
                self.logger.log_writer.error(f"Delete ssl pair error, {e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        ngx_config_rollback()
        return status_code_500("delete.ssl.fail.server")

    def read_ssl_detail(self, ssl_id):
        ssl_detail = self.session.query(SSLBase).filter(SSLBase.id.__eq__(ssl_id)).first()
        if ssl_detail:
            ssl_base = {
                "id": ssl_detail.id,
                "ssl_name": ssl_detail.ssl_name,
                "ssl_description": ssl_detail.ssl_description,
                "ssl_key": ssl_detail.ssl_key,
                "ssl_cert": ssl_detail.ssl_cert
            }
            return ssl_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            self.logger.log_writer.error(f"Query ssl error, {ssl_detail}")
            return {}
