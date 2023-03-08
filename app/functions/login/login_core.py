from datetime import datetime, timedelta
import uuid

import pyotp
import pytz
from flask import request
from flask_jwt_extended import (create_access_token, create_refresh_token, get_jwt_identity, get_raw_jwt)

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.ORMBase import  ORMSession_alter
from app.libraries.data_format.change_data import md5
from app.libraries.http.response import status_code_200, status_code_400, status_code_500, status_code_401
from app.libraries.logger import c_logger
from app.model import UserBase, DeadTokenBase, SessionManagerBase
from app.model.ClickhouseModel import MonitorLogin
from app.libraries.system.log_action import log_setting
import jwt


MAX_LOGIN_ATTEMPT = 5  # times
IP_BLOCK_LOGIN_TIME = 1  # min


def verify_input(input_json_data):
    verify = ""
    if "user_name" not in input_json_data:
        verify += "user_name not found, "
    if "password" not in input_json_data:
        verify += "password not found, "
    return verify


class Login(object):
    def __init__(self):
        self.session,self.engine_connect  = ORMSession_alter()
        self.cdb = ClickhouseBase()
        self.Ho_Chi_Minh = pytz.timezone("Asia/Ho_Chi_Minh")
        self.logger = c_logger("login_core")

    def number_of_login_attempt(self, ip_address):
        filter_time = datetime.utcnow() - timedelta(minutes=IP_BLOCK_LOGIN_TIME)
        number_of_attempt = MonitorLogin.objects_in(self.cdb).filter(MonitorLogin.ip_address.__eq__(ip_address),
                                                                     MonitorLogin.login_status.__eq__(0),
                                                                     MonitorLogin.datetime > filter_time).count()
        return number_of_attempt

    def login(self, input_json_data):
        ip_address = request.headers.get('X-Forwarded-For')
        if self.number_of_login_attempt(ip_address) >= MAX_LOGIN_ATTEMPT:
            log_setting(action="Login", status=0, description=f'{input_json_data["user_name"]} Login failed! - client is blocked')
            return status_code_400('login.error.block.client')
        json_error = verify_input(input_json_data)
        if json_error != "":
            self.logger.log_writer.error(f"Json data error,{json_error}")
            log_setting(action="Login", status=0, description=f'{input_json_data["user_name"]} Login failed! - bad request')
            return status_code_400("login.error.client")
        login_check = self.session.query(UserBase).filter(
            UserBase.user_name.__eq__(input_json_data["user_name"]),
            UserBase.password.__eq__(md5(input_json_data["password"]))).first()
        if login_check:
            if login_check.two_fa_status == 1 and "otp" not in input_json_data:
                return status_code_401("OTP required")
            elif "otp" in input_json_data:
                otp_check = pyotp.TOTP(login_check.secret_key)
                if otp_check.now() == input_json_data["otp"]:
                    access_token = create_access_token(identity=login_check.id)
                    refresh_token = create_refresh_token(identity=login_check.id)
                    json_access_jwt = jwt.decode(access_token, "sc_key")
                    json_refresh_jwt = jwt.decode(refresh_token, "sc_key")
                    session_obj = SessionManagerBase(jti_access=json_access_jwt.get("jti"), exp_access=json_access_jwt.get("exp"), ip_address=ip_address, 
                                                    login_time=self.Ho_Chi_Minh.localize(datetime.now()),account=input_json_data["user_name"],
                                                    jti_refresh=json_refresh_jwt.get("jti"), exp_refresh=json_refresh_jwt.get("expired_time"))
                    self.session.add(session_obj)
                    self.session.flush()
                    self.session.commit()
                    log_setting(action="Login", status=1, description=f'{input_json_data["user_name"]} Login success!')
                    return status_code_200("Authenticated", {
                        "user_name": login_check.user_name,
                        "full_name": login_check.full_name,
                        "id": login_check.id,
                        "access_token": access_token,
                        "refresh_token": refresh_token
                    })
            else:
                access_token = create_access_token(identity=login_check.id)
                refresh_token = create_refresh_token(identity=login_check.id)
                login_obj = MonitorLogin(ip_address=ip_address, username=input_json_data['user_name'], login_status=1)
                log_setting(action="Login", status=1, description=f'{input_json_data["user_name"]} Login success!')
                self.cdb.insert([login_obj])
                self.session.close()
                self.engine_connect.dispose()
                json_access_jwt = jwt.decode(access_token, "sc_key")
                json_refresh_jwt = jwt.decode(refresh_token, "sc_key")
                session_obj = SessionManagerBase(jti_access=json_access_jwt.get("jti"), exp_access=json_access_jwt.get("exp"), ip_address=ip_address, 
                                                 login_time=self.Ho_Chi_Minh.localize(datetime.now()),account=input_json_data["user_name"],
                                                 jti_refresh=json_refresh_jwt.get("jti"), exp_refresh=json_refresh_jwt.get("exp"))
                self.session.add(session_obj)
                self.session.flush()
                self.session.commit()
                return status_code_200("Authenticated", {
                    "user_name": login_check.user_name,
                    "full_name": login_check.full_name,
                    "id": login_check.id,
                    "access_token": access_token,
                    "refresh_token": refresh_token
                })
        else:
            login_obj = MonitorLogin(ip_address=ip_address, username=input_json_data['user_name'], login_status=0)
            log_setting(action="Login", status=0, description=f"{input_json_data['user_name']} Login failed!")
            self.cdb.insert([login_obj])
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("login.error.client")

    def logout_access_token(self):
        jti = get_raw_jwt()["jti"]
        token_obj = DeadTokenBase(token=jti, type="access")
        self.session.add(token_obj)
        self.session.flush()
        try:
            self.session.commit()
        except Exception as e:
            self.logger.log_writer.error(f"logout fail, {e}")
            return status_code_500("logout.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("logout.success", jti)

    def logout_refresh_token(self):
        jti = get_raw_jwt()["jti"]
        refresh_obj = DeadTokenBase(token=jti, type="refresh")
        self.session.add(refresh_obj)
        self.session.flush()
        try:
            self.session.commit()
        except Exception as e:
            self.logger.log_writer.error(f"logout refresh token fail, {e}")
            return status_code_500("logout.refresh.token.fail.server")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("logout.refresh.token.success", jti)

    def refresh_user_token(self):
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return status_code_200("", {"access_token": access_token})

    def turn_on_two_factor_authentication(self, two_fa_json_data, user_id):
        user_detail = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        if user_detail:
            if md5(two_fa_json_data['password']) == user_detail.password:
                key = pyotp.parse_uri(two_fa_json_data['url']).secret
                otp = pyotp.TOTP(key)
                print(otp.now())
                if two_fa_json_data['otp'] == otp.now():
                    user_detail.two_fa_status = 1
                    user_detail.secret_key = key
                    self.session.flush()
                    try:
                        self.session.commit()
                        return status_code_200("add.2fa.success", {})
                    except Exception as e:
                        raise e
                        self.logger.log_writer.error(f"add 2fa fail, {e}")
                    finally:
                        self.session.close()
                        self.engine_connect.dispose()
                else:
                    return status_code_400("OTP Was wrong")
            else:
                return status_code_400("Password was wrong ")
            return status_code_500("add.2fa.fail.server")
        else:
            return status_code_400("No User exist")

    def turn_off_two_factor_authentication(self, two_fa_json_data, user_id):
        user_detail = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        if user_detail:
            user_detail.two_fa_status = two_fa_json_data["two_fa_status"]
            user_detail.secret_key = ""
            self.session.flush()
            try:
                self.session.commit()
                return status_code_200("turn.off.2fa.success", {})
            except Exception as e:
                self.logger.log_writer.error(f"turn off 2fa fail, {e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        else:
            return status_code_400("No user exist")

    def create_two_factor_authentication(self, user_id):
        print(user_id)
        user_detail = self.session.query(UserBase).filter(UserBase.id.__eq__(user_id)).first()
        if user_detail:
            secret_key = pyotp.random_base32()
            url = pyotp.totp.TOTP(secret_key). \
                provisioning_uri(name=f'{user_detail.user_name}', issuer_name='Secure App')
            return status_code_200("get.otp.url.success", url)
        else:
            self.session.close()
            self.engine_connect.dispose()
            return status_code_400("get.otp.url.fail")
