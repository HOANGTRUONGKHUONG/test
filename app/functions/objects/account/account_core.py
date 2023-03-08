from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import *
from app.libraries.data_format.validate_data import *
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import AccountBase, ReportAccountBase, ScheduleAccountBase


def verify_input(account_json_data):
    verify = ""
    # check length name
    if len(account_json_data["name"]) not in range(9, 31):
        verify += f"account name {account_json_data['name']} is not validate, "

    # check email
    if not is_email(account_json_data["email"]):
        verify += f"Email {account_json_data['email']} is not validate"
    # check phone
    if account_json_data["phone"].isdigit():
        if len(account_json_data["phone"]) not in range(10, 12):
            verify += f"phone number {account_json_data['phone_number']} is not validate, "
    else:
        verify += f"phone number {account_json_data['phone']} is not validate, "
    return verify


class Account(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("account")

    def get_all_account(self, http_parameters):
        list_account_id, number_of_account = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                 AccountBase)

        all_account_base_data = []
        for account_id in list_account_id:
            all_account_base_data.append(self.read_account_detail(account_id.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_account_base_data, number_of_account, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def add_new_account(self, account_json_data):
        json_error = verify_input(account_json_data)
        if json_error:
            print(json_error)
            self.logger.log_writer.error(f"json data error, {json_error}")
            return status_code_400("add.new.account.fail.client")

        account_obj = AccountBase(name=account_json_data["name"],
                                  email=account_json_data["email"], phone_number=account_json_data["phone"])
        self.session.add(account_obj)
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting("Account", 1, "Add new account")
            data = self.read_account_detail(account_obj.id)
        except Exception as e:
            self.logger.log_writer.error(f"Add account fail,{e}")
            monitor_setting = log_setting("Account", 0, "Add new account failed")
            return status_code_500("post.account.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("post.account.success", data)

    def get_account_detail(self, account_id):
        account_detail = self.read_account_detail(account_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(account_detail):
            return status_code_200("get.account.success", account_detail)
        else:
            return status_code_400("get.account.fail.client")

    def edit_account(self, account_id, account_json_data):
        json_error = verify_input(account_json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            return status_code_400("put.account.fail.client")
        account_detail = self.read_account_detail(account_id)
        account_detail.update(account_json_data)
        account_obj = self.session.query(AccountBase).filter(AccountBase.id.__eq__(account_id)).one()
        account_obj.name = account_detail["name"]
        account_obj.email = account_detail["email"]
        account_obj.phone_number = account_detail["phone"]
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting("Account", 1, "Edit account")
            data = self.read_account_detail(account_id)
        except Exception as e:
            self.logger.log_writer.error(f"Edit account fail, {e}")
            monitor_setting = log_setting("Account", 0, "Edit account failed")
            return status_code_500("put.account.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("put.account.success", data)

    def delete_account(self, account_id):
        self.session.query(ScheduleAccountBase).filter(ScheduleAccountBase.account_id.__eq__(account_id)).delete()
        self.session.query(ReportAccountBase).filter(ReportAccountBase.object_account_id.__eq__(account_id)).delete()
        self.session.query(AccountBase).filter(AccountBase.id.__eq__(account_id)).delete()
        try:
            self.session.commit()
            monitor_setting = log_setting("Account", 1, "Delete account")
        except Exception as e:
            self.logger.log_writer.error(f"Delete account fail,{e}")
            monitor_setting = log_setting("Account", 0, "Delete account failed")
            return status_code_500("delete.account.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("delete.account.success", {})

    def read_account_detail(self, account_id):
        account_detail = self.session.query(AccountBase).filter(AccountBase.id.__eq__(account_id)).first()
        self.session.close()
        self.engine_connect.dispose()
        if account_detail:
            account_base_data = {
                "id": account_detail.id,
                "name": account_detail.name,
                "email": account_detail.email,
                "phone": account_detail.phone_number
            }
            return account_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}
            