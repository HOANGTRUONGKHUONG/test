import datetime
import os
import shutil

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.system.shell import run_command
from app.model import BackupScheduleBase, PeriodBase
from app.setting import NGINX_CONFIG_DIR, NETWORK_CONFIG_DIR, DATABASE_PASSWORD

DATE_FORMAT = '%Y-%m-%d'
FILE_PATH = "/home/bwaf/backup_data"


# TODO: save file path in file (do not hard code)

def restore(file_name):
    # Remove old config
    # update new config
    # shutil.copytree(f"{file_path}/{file_name}/conf.d", f"{NGINX_CONFIG_DIR}/conf.d")
    # shutil.copytree(f"{file_path}/{file_name}/group_website", f"{NGINX_CONFIG_DIR}/group_website")
    # shutil.copytree(f"{file_path}/{file_name}/ssl", f"{NGINX_CONFIG_DIR}/ssl")
    # shutil.copytree(f"{file_path}/{file_name}/modsec", f"/home/waf_lab/modsec")
    # shutil.copytree(f"{file_path}/{file_name}", f"{NGINX_CONFIG_DIR}/modsec.conf")
    # shutil.copytree(f"{file_path}/{file_name}", f"{NGINX_CONFIG_DIR}/proxy.conf")
    # shutil.copytree(f"{file_path}/{file_name}/snippets", f"{NGINX_CONFIG_DIR}/snippets")
    pass


def backup(file_name):
    if not os.path.exists(FILE_PATH):
        os.mkdir(FILE_PATH)
    run_command(f"mkdir {FILE_PATH}/{file_name}")
    # WAF and IPS (/usr/local/openresty/nginx)
    shutil.copytree(f"{NGINX_CONFIG_DIR}/conf.d", f"{FILE_PATH}/{file_name}/conf.d")
    shutil.copytree(f"{NGINX_CONFIG_DIR}/group_website", f"{FILE_PATH}/{file_name}/group_website")
    shutil.copytree(f"{NGINX_CONFIG_DIR}/ssl", f"{FILE_PATH}/{file_name}/ssl")
    shutil.copytree(f"{NGINX_CONFIG_DIR}/modsec", f"{FILE_PATH}/{file_name}/modsec")
   # shutil.copyfile(f"{NGINX_CONFIG_DIR}/modsec.conf", f"{FILE_PATH}/{file_name}/modsec.conf")
    shutil.copyfile(f"{NGINX_CONFIG_DIR}/conf/nginx.conf", f"{FILE_PATH}/{file_name}/nginx.conf")
    shutil.copyfile(f"{NGINX_CONFIG_DIR}/proxy.conf", f"{FILE_PATH}/{file_name}/proxy.conf")
    #shutil.copytree(f"{NGINX_CONFIG_DIR}/snippets", f"{FILE_PATH}/{file_name}/snippets")
    # Interface
    shutil.copytree(f"{NETWORK_CONFIG_DIR}", f"{FILE_PATH}/{file_name}/netplan")
    # Database
    run_command(f"mysqldump -u root -p{DATABASE_PASSWORD} bwaf > {FILE_PATH}/{file_name}/bwaf_backup.sql")
    # W3af
    shutil.copytree(f"/home/ubuntu/w3af", f"{FILE_PATH}/{file_name}/w3af")
    # Front-end data
    shutil.copytree(f"/home/bwaf/dist", f"{FILE_PATH}/{file_name}/dist")
    run_command(f"zip -r {FILE_PATH}/{file_name}.zip {FILE_PATH}/{file_name} ")
    run_command(f"rm -r {FILE_PATH}/{file_name}")


if __name__ == '__main__':
    session,engine_connect = ORMSession_alter()
    today = datetime.datetime.today().strftime(DATE_FORMAT)
    order = BackupScheduleBase.__table__.columns['id']
    order = order.desc()
    shedule = session.query(BackupScheduleBase).order_by(order).first()
    if datetime.datetime.today() >= shedule.datetime:
        input_data = shedule.file_name + "+" + shedule.account + "+" + str(today) + "+" \
                     + str(shedule.period_id) + "+schedule"
        period = session.query(PeriodBase).filter(PeriodBase.id.__eq__(shedule.period_id)).first()
        if period.period_name == "Daily":
            backup(input_data)
        if period.period_name == "Weekly":
            if today.weekday() == 0:
                backup(input_data)
        if period.period_name == "Yearly":
            if today.day == 1 and today.month == 1:
                backup(input_data)
        if period.period_name == "Monthly":
            if today.day == 1:
                backup(input_data)
    session.close()
    engine_connect.dispose()
