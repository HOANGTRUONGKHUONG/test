from flask import request
from flask_jwt_extended import get_jwt_identity

from app.functions.user.user_core import User
from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.system.sys_time import get_current_time
from app.model.ClickhouseModel import MonitorSetting


# action: text
# status: int
# description: text
def log_setting(action, status, description):
    ip_address = request.headers.get('X-Forwarded-For')
    current_time = get_current_time()
    current_user = get_jwt_identity()
    user = User()
    try:
        username = user.read_user_detail(current_user)["user_name"]
    except Exception as e:
        username = ""
    db = ClickhouseBase()
    monitor_setting_obj = MonitorSetting(user_name=username, ip_address=ip_address,
                                         action=action, status=status, description=description)
    log_setting_status = True
    log_setting_error = None
    try:
        db.insert([monitor_setting_obj])
    except Exception as e:
        log_setting_status = False
        log_setting_error = e
    finally:
        return {
            "log_setting": log_setting_status, "log_setting_error": log_setting_error, "datetime": current_time,
            "user_name": username, "ip_address": ip_address, "action": action, "status": status,
            "description": description
        }
