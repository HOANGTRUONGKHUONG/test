from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.validate_data import is_email
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_500, status_code_200
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import MailSenderBase, MailServerBase
#import validators


def verify_input(sender_json_data):
    verify = ""
    # check length name
    # if len(sender_json_data["name"]) not in range(9, 31):
    #    verify += f"account name {sender_json_data['name']} is not validate, "
    # check email
    if not is_email(sender_json_data['email']):
        verify += f"Email {sender_json_data['email']} is not validate, "
    
    # if not validators.email(sender_json_data['email']):
    #     verify += f"Email {sender_json_data['email']} is not validate, "
    # check password
    # if not is_password(sender_json_data["password"]):
    #     verify += f"Password {sender_json_data['password']} is not validate, "

    if len(sender_json_data["password"]) not in range(9,50):
        verify += f"Password {sender_json_data['password']} is not validate, "


    return verify


class MailSender(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("object_mail_sender")

    def get_all_mail_sender(self, http_parameters):
        list_sender_id, number_of_mail_sender = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                    MailSenderBase)
    
        all_mail_sender_base_data = []
        for sender in list_sender_id:
            all_mail_sender_base_data.append(self.read_mail_sender_detail(sender.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(
            all_mail_sender_base_data, number_of_mail_sender, http_parameters["limit"], http_parameters["offset"]
        ))

    def add_new_mail_sender(self, sender_json_data):
        json_error = verify_input(sender_json_data)
        if json_error:
            self.logger.log_writer.error(f"Json data error, {json_error}")
            return status_code_400("post.mail.sender.fail.client")
        sender_obj = MailSenderBase(email=sender_json_data["email"],
                                    password=sender_json_data["password"], server_id=sender_json_data["mail_server_id"])
        self.session.add(sender_obj)
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting(action="Mail sender", status=1, description="Add new mail sender")
            return status_code_200("post.mail.sender.success", self.read_mail_sender_detail(sender_obj.id))
        except Exception as e:
         #   raise e
            monitor_setting = log_setting(action="Mail sender", status=0, description="Add new mail sender failed")
            self.logger.log_writer.error(f"Add mail sender fail,{e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("post.mail.sender.fail.server")

    def get_mail_sender_detail(self, sender_id):
        sender_detail = self.read_mail_sender_detail(sender_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(sender_detail):
            return status_code_200("get.mail.sender.success", sender_detail)
        else:
            return status_code_400("get.mail.sender.fail.client")

    def edit_mail_sender(self, sender_id, sender_json_data):
        json_error = verify_input(sender_json_data)
        if json_error:
            self.logger.log_writer.error(f"Json data error, {json_error}")
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.mail.sender.fail.client")
        sender_detail = self.read_mail_sender_detail(sender_id)
        sender_detail.update(sender_json_data)

        sender_obj = self.session.query(MailSenderBase).filter(MailSenderBase.id.__eq__(sender_id)).one()

        sender_obj.email = sender_detail["email"]
        sender_obj.password = sender_detail["password"]
        sender_obj.server_id = sender_detail["mail_server_id"]
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting(action="Mail sender", status=1, description="Edit mail sender")
            return status_code_200("put.mail.sender.success", self.read_mail_sender_detail(sender_id))
        except Exception as e:
            self.logger.log_writer.error(f"Edit mail sender fail, {e}")
            monitor_setting = log_setting(action="Mail sender", status=0, description="Edit mail sender failed")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.mail.sender.fail.server")

    def delete_mail_sender(self, sender_id):
        try:
            self.session.query(MailSenderBase).filter(MailSenderBase.id.__eq__(sender_id)).delete()
            try:
                self.session.commit()
                monitor_setting = log_setting(action="Mail sender", status=1, description="Delete mail sender")
            except Exception as e:
                self.logger.log_writer.error(f"Delete mail sender fail, {e}")
                monitor_setting = log_setting(action="Mail sender", status=0, description="Delete mail sender failed")
                return status_code_500("delete.mail.sender.fail.server")
            finally:
                self.session.close()
                self.engine_connect.dispose()
            return status_code_200("delete.mail.sender.success", {})
        except Exception as e:
            monitor_setting = log_setting(action="Mail sender", status=0, description="Delete mail sender failed")
            self.logger.log_writer.error(f"Delete mail sender faile client, {e}")
            return status_code_400("delete.used.mail.sender.fail.client")
        finally:
            self.session.close()
            self.engine_connect.dispose()

    def read_mail_sender_detail(self, sender_id):
        mail_sender_detail = self.session.query(MailSenderBase).outerjoin(MailServerBase). \
            filter(MailSenderBase.id.__eq__(sender_id)).first()
        if mail_sender_detail:
            mail_sender_base_data = {
                "id": mail_sender_detail.id,
                "email": mail_sender_detail.email,
                "password": mail_sender_detail.password,
                "mail_server_id": mail_sender_detail.mail_server.id if mail_sender_detail.mail_server is not None else None,
                "mail_server_name": mail_sender_detail.mail_server.name if mail_sender_detail.mail_server is not None else None
            }
            return mail_sender_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
