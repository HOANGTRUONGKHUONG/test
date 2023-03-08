from datetime import datetime

import pyotp

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.change_data import md5
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.validate_data import is_right_datetime, is_email, is_password
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_200, status_code_500
from app.libraries.logger import c_logger
from app.libraries.system.sys_time import datetime_to_str, get_current_time
from app.model import UserBase

PASSWORD_HIDER = "**************************"


def verify_user(user_json_data):
    verify = ""
    # check Name
    if "name" in user_json_data and user_json_data["name"] is not None and len(user_json_data["name"]) > 500:
        verify += "Name too long, "
    # check date of birthday
    if "date_of_birthday" in user_json_data and user_json_data["date_of_birthday"] is not None:
        if is_right_datetime(user_json_data["date_of_birthday"]):
            verify += "date_of_birthday is not validate, "
    # check user name
    if len(user_json_data["user_name"]) > 255:
        verify += "User name too long, "
    # check password
    if "password" in user_json_data and user_json_data["password"] != PASSWORD_HIDER \
            and not is_password(user_json_data["password"]):
        verify += "password error, "
    # check phone number
    if user_json_data["phone_number"].isdigit():
        if len(user_json_data["phone_number"]) not in range(10, 12):
            verify += f"phone number {user_json_data['phone_number']} is not validate, "
    else:
        verify += f"phone number {user_json_data['phone_number']} is not validate, "
    # check email
    if not is_email(user_json_data["email"]):
        verify += f"Email {user_json_data['email']} is not validate, "
    return verify


class User(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("user").log_writer

    def get_all_user(self, http_parameters):
        list_user_id, number_of_user = get_id_single_table(self.session, self.logger, http_parameters, UserBase)

        all_user_base_data = []
        for user_id in list_user_id:
            all_user_base_data.append(self.read_user_detail(user_id.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_user_base_data, number_of_user, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def add_new_user(self, user_json_data):
        json_error = verify_user(user_json_data)
        if json_error:
            self.logger.error("Json data error,{error}".format(error=json_error))
            return status_code_400("post.user.fail.client")
        user_obj = UserBase(user_name=user_json_data["user_name"], password=md5(user_json_data["password"]),
                            phone_number=user_json_data["phone_number"], email=user_json_data["email"],
                            can_edit=user_json_data["can_edit"], date_create=get_current_time(),
                            secret_key="", two_fa_status=0, ip_conn=1, last_login_at=get_current_time())
        self.session.add(user_obj)
        self.session.flush()
        try:
            self.session.commit()
            return status_code_200("post.user.success", self.read_user_detail(user_obj.id))
        except Exception as e:
            raise e
            self.logger.error(f"Add user fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("post.user.fail.server")

    def get_user_detail(self, user_id):
        user_detail = self.read_user_detail(user_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(user_detail):
            return get_status_code_200(user_detail)
        else:
            return status_code_400("get.user.fail.client")

    def edit_user(self, user_id, user_json_data):
        # only use by admin
        json_error = verify_user(user_json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            return status_code_400("put.user.fail.client")
        user_detail = self.read_user_detail(user_id)
        user_detail.update(user_json_data)
        user_obj = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).one()
        if user_detail["user_name"] != user_obj.user_name:
            return status_code_200("you cant change user_name", {})
        if user_detail["password"] != PASSWORD_HIDER:
            user_obj.password = md5(user_detail["password"])
        else:
            user_obj.password = user_obj.password
        user_obj.phone_number = user_detail["phone_number"]
        user_obj.email = user_detail["email"]
        user_obj.can_edit = user_detail["can_edit"]
        self.session.flush()
        try:
            self.session.commit()
            return status_code_200("put.user.success", self.read_user_detail(user_id))
        except Exception as e:
            self.logger.error(f"Edit user fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.user.fail.server")

    def delete_user(self, user_id):
        a = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        if a:
            self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).delete()
            try:
                self.session.commit()
                return status_code_200("delete.user.success", {})
            except Exception as e:
                self.logger.error(f"Delete user fail, {e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()
            return status_code_500(f"delete.user.fail.server")
        else:
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("delete.user.fail.client")

    def read_user_detail(self, user_id):
        user_detail = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        if user_detail:
            user_base_data = {
                "id": user_detail.id,
                "user_name": user_detail.user_name,
                "password": PASSWORD_HIDER,
                "phone_number": user_detail.phone_number,
                "can_edit": user_detail.can_edit,
                "email": user_detail.email
            }
            return user_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def read_detail_profile(self, user_id):
        user_detail = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        if user_detail:
            user_base_data = {
                "user_name": user_detail.user_name,
                "sex": user_detail.sex,
                "phone_number": user_detail.phone_number,
                "date_of_birthday": datetime_to_str(user_detail.date_of_birth),
                "email": user_detail.email,
                "date_created": datetime_to_str(user_detail.date_create),
                "image_link": user_detail.image_link,
                "name": user_detail.full_name,
                "two_fa_status": user_detail.two_fa_status
            }
            return user_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def edit_profile(self, user_id, user_json_data):
        json_error = verify_user(user_json_data)
        if json_error:
            self.logger.error(f"json data error, {json_error}")
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.profile.fail.client")
        user_detail = self.read_detail_profile(user_id)
        user_detail.update(user_json_data)
        user_obj = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        user_obj.full_name = user_detail["name"]
        user_obj.phone_number = user_detail["phone_number"]
        user_obj.email = user_detail["email"]
        user_obj.sex = user_detail["sex"]
        user_obj.image_link = user_detail["image_link"]
        user_obj.date_of_birth = datetime.strptime(user_detail["date_of_birthday"], '%d/%m/%Y')
        user_obj.date_create = user_detail["date_created"]
        self.session.flush()
        try:
            self.session.commit()
            return status_code_200("put.profile.success", self.read_detail_profile(user_id))
        except Exception as e:
            self.logger.error(f"Edit user fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.profile.fail.server")

    def edit_password(self, user_id, user_json_data):
        if not is_password(user_json_data["password"]):
            self.logger.error(f"Password is not validate")
            return status_code_400("put.password.fail.client")
        user_obj = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).one()
        if user_obj.password == md5(user_json_data["old_password"]) and user_obj.password != md5(
                user_json_data["password"]):
            user_obj.password = md5(user_json_data["password"])
        else:
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("put.password.fail.client")
        self.session.flush()
        try:
            self.session.commit()
            return status_code_200("put.password.success", md5(user_obj.password))
        except Exception as e:
            self.logger.error(f"Edit user fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.password.fail.server")

