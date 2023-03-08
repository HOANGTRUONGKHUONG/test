from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.model import WAFAlertBase, AlertTypeBase, WAFAlertAccountBase, AccountBase, SMSSenderBase, MailSenderBase


class WAFAlertConfiguration(object):
    def __init__(self):
        self.logger = c_logger("waf_alert").log_writer
        self.session, self.engine_connect = ORMSession_alter()

    def get_group_website_alert_detail(self, group_website_id):
        alert_detail = self.read_alert_detail(group_website_id)
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200({"data": alert_detail})

    def get_list_alert_id(self, alert_id):
        list_account_id = []
        list_alert = self.session.query(WAFAlertAccountBase, AccountBase).outerjoin(AccountBase). \
            filter(WAFAlertAccountBase.waf_alert_id.__eq__(alert_id)).all()
        for alert_item in list_alert:
            data = {
                "id": alert_item.AccountBase.id,
                "name": alert_item.AccountBase.name,
                "email": alert_item.AccountBase.email,
                "phone": alert_item.AccountBase.phone_number
            }
            list_account_id.append(data)
        self.session.close()
        self.engine_connect.dispose()
        return list_account_id

    def add_new_alert(self, alert_type_id, json_data, group_website_id):
        if json_data["alert_type"] == "mail":
            alert_obj = WAFAlertBase(alert_type_id=alert_type_id, barrier=json_data["barrier"],
                                     interval_time=json_data["time"],
                                     mail_sender_id=json_data["mail_sender"]["id"],
                                     status=json_data["state"], group_website_id=group_website_id)
            self.session.add(alert_obj)
            self.session.flush()
            for account in json_data["account"]:
                alert_account_obj = WAFAlertAccountBase(waf_alert_id=alert_obj.id, account_id=account["id"])
                self.session.add(alert_account_obj)
                self.session.flush()
        else:
            alert_obj = WAFAlertBase(alert_type_id=alert_type_id, barrier=json_data["barrier"],
                                     interval_time=json_data["time"],
                                     sms_sender_id=json_data["sms_sender"]["id"],
                                     status=json_data["state"], group_website_id=group_website_id)
            self.session.add(alert_obj)
            self.session.flush()
            for account in json_data["account"]:
                alert_account_obj = WAFAlertAccountBase(waf_alert_id=alert_obj.id, account_id=account["id"])
                self.session.add(alert_account_obj)
                self.session.flush()

    def change_group_website_alert(self, group_website_id, json_data):
        alert_data = self.session.query(WAFAlertBase).outerjoin(AlertTypeBase). \
            filter(WAFAlertBase.group_website_id.__eq__(group_website_id))
        alert_type_id = self.session.query(AlertTypeBase). \
            filter(AlertTypeBase.type_name.__eq__(json_data["alert_type"])).first()
        if json_data["alert_type"] == "mail":
            # mail
            alert_mail = alert_data.filter(AlertTypeBase.type_name.__eq__("mail")).first()
            if alert_mail:
                # edit => remove exist
                self.session.query(WAFAlertBase).filter(WAFAlertBase.group_website_id.__eq__(group_website_id)). \
                    filter(WAFAlertBase.alert_type_id.__eq__(alert_type_id.id)).delete()
            # add new
            self.add_new_alert(alert_type_id.id, json_data, group_website_id)

        elif json_data["alert_type"] == "sms":
            # sms
            alert_sms = alert_data.filter(AlertTypeBase.type_name.__eq__("sms")).first()

            if alert_sms:
                # edit => remove exist
                self.session.query(WAFAlertBase).filter(WAFAlertBase.group_website_id.__eq__(group_website_id)). \
                    filter(WAFAlertBase.alert_type_id.__eq__(alert_type_id.id)).delete()
            # add new
            self.add_new_alert(alert_type_id.id, json_data, group_website_id)
        try:
            self.session.commit()
            return status_code_200("put.waf.alert.success", self.read_alert_detail(group_website_id))
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Add alert fail, {e}")
        finally:
            self.session.close()
            self.engine_connect.dispose()
        return status_code_500("put.waf.alert.fail.server")

    def read_alert_detail(self, group_website_id):
        alert_detail = {}
        alert_data = self.session.query(WAFAlertBase).outerjoin(AlertTypeBase). \
            filter(WAFAlertBase.group_website_id.__eq__(group_website_id))
        # mail
        alert_mail = alert_data.filter(AlertTypeBase.type_name.__eq__("mail")).first()
        if alert_mail:
            mail_name = self.session.query(MailSenderBase). \
                filter(MailSenderBase.id.__eq__(alert_mail.mail_sender_id)).first()
            alert_detail["alert_mail"] = {
                "barrier": alert_mail.barrier,
                "time": alert_mail.interval_time,
                "mail_sender": {
                    "id": alert_mail.mail_sender_id,
                    "name": mail_name.email
                },
                "account": self.get_list_alert_id(alert_mail.id),
                "state": alert_mail.status
            }
        else:
            alert_detail["alert_mail"] = {
                "barrier": None,
                "time": None,
                "mail_sender": {},
                "account": [],
                "state": None
            }

        # sms
        alert_sms = alert_data.filter(AlertTypeBase.type_name.__eq__("sms")).first()

        if alert_sms:
            sms_name = self.session.query(SMSSenderBase). \
                filter(SMSSenderBase.id.__eq__(alert_sms.sms_sender_id)).first()
            alert_detail["alert_sms"] = {
                "barrier": alert_sms.barrier,
                "time": alert_sms.interval_time,
                "sms_sender": {
                    "id": alert_sms.sms_sender_id,
                    "name": sms_name.sms_sender_name
                },
                "account": self.get_list_alert_id(alert_sms.id),
                "state": alert_sms.status
            }
        else:
            alert_detail["alert_sms"] = {
                "barrier": None,
                "time": None,
                "sms_sender": {},
                "account": [],
                "state": None
            }
        self.session.close()
        self.engine_connect.dispose()
        return alert_detail
