from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import reformat_data_with_paging
from app.libraries.data_format.validate_data import is_right_datetime, is_datetime_right
from app.libraries.http.response import get_status_code_200, status_code_400, status_code_500, status_code_200
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import ScanScheduleBase, ScheduleAccountBase, ScheduleWebsiteBase, AccountBase, WebsiteBase


class ScanSchedule(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("Scan_schedule").log_writer

    def get_all_schedule(self, http_parameters):
        list_schedule_id, number_of_schedule = get_id_single_table(self.session, self.logger, http_parameters,
                                                                   ScanScheduleBase)

        all_schedule_base_data = []
        for schedules in list_schedule_id:
            all_schedule_base_data.append(self.read_schedule(schedules.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_schedule_base_data, number_of_schedule, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def create_schedule(self, schedule_json_data):
        if not is_datetime_right(schedule_json_data["start_in"]):
            return status_code_400("post.schedule.scan.fail.client")
        schedule_data = ScanScheduleBase(period_id=schedule_json_data["period_id"],
                                         start_in=schedule_json_data["start_in"],
                                         mail_sender_id=schedule_json_data["mail_sender_id"])
        self.session.add(schedule_data)
        self.session.flush()
        try:
            self.session.commit()
        except Exception as e:
            self.logger.error(e)
            return status_code_500("post.schedule.scan.fail.server")
        for i in schedule_json_data["website_id"]:
            schedule_website_obj = ScheduleWebsiteBase(website_id=i, schedule_id=schedule_data.id)
            self.session.add(schedule_website_obj)
        for i in schedule_json_data["account_id"]:
            schedule_account_obj = ScheduleAccountBase(account_id=i, schedule_id=schedule_data.id)
            self.session.add(schedule_account_obj)
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting(action="Web Scan", status=1, description="Create web scan schedule")
        except Exception as e:
            self.logger.error(e)
            monitor_setting = log_setting(action="Web Scan", status=0, description="Create web scan schedule failed")
            return status_code_500("post.schedule.scan.fail.server")
        data = self.read_schedule(schedule_data.id)
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("post.schedule.scan.success",
                               data)

    def get_schedule_detail(self, schedule_id):
        schedule_detail = self.read_schedule(schedule_id)
        if bool(schedule_detail):
            return status_code_200("get.one.schedule.success", schedule_detail)
        else:
            return status_code_400("get.one.schedule.fail.client")

    def edit_schedule(self, schedule_json_data, schedule_id):
        if not is_datetime_right(schedule_json_data["start_in"]):
            return status_code_400("put.schedule.scan.fail.client")
        schedule_data = self.read_schedule(schedule_id)
        schedule_data.update(schedule_json_data)
        schedule_obj = self.session.query(ScanScheduleBase).filter(ScanScheduleBase.id.__eq__(schedule_id)).one()
        schedule_obj.period_id = schedule_data["period_id"]
        schedule_obj.start_in = schedule_data["start_in"]
        schedule_obj.mail_sender_id = schedule_data["mail_sender_id"]
        self.session.query(ScheduleAccountBase). \
            filter(ScheduleAccountBase.schedule_id.__eq__(schedule_id)).delete()
        self.session.query(ScheduleWebsiteBase). \
            filter(ScheduleWebsiteBase.schedule_id.__eq__(schedule_id)).delete()
        self.session.flush()
        for i in schedule_json_data["website_id"]:
            schedule_website_obj = ScheduleWebsiteBase(website_id=i, schedule_id=schedule_obj.id)
            self.session.add(schedule_website_obj)
        for i in schedule_json_data["account_id"]:
            schedule_account_obj = ScheduleAccountBase(account_id=i, schedule_id=schedule_obj.id)
            self.session.add(schedule_account_obj)
        try:
            self.session.commit()
            monitor_setting = log_setting(action="Web Scan", status=1, description="Edit web scan schedule")
        except Exception as e:
            self.logger.error(f"Edit schedule fail, {e}")
            monitor_setting = log_setting(action="Web Scan", status=0, description="Edit web scan schedule failed")
            return status_code_500("put.schedule.fail.server")
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("put.schedule.success", self.read_schedule(schedule_id))

    def delete_schedule(self, schedule_id):
        self.session.query(ScheduleWebsiteBase).filter(ScheduleWebsiteBase.schedule_id.__eq__(schedule_id)).delete()
        self.session.query(ScheduleAccountBase).filter(ScheduleAccountBase.schedule_id.__eq__(schedule_id)).delete()
        self.session.query(ScanScheduleBase).filter(ScanScheduleBase.id.__eq__(schedule_id)).delete()
        try:
            self.session.commit()
            monitor_setting = log_setting(action="Web Scan", status=1, description="Delete web scan schedule")
        except Exception as e:
            self.logger.error(f"Delete schedule fail, {e}")
            monitor_setting = log_setting(action="Web Scan", status=0, description="Delete web scan schedule failed")
            return status_code_500(f"Delete.schedule.fail.server")
        self.session.close()
        self.engine_connect.dispose()
        return status_code_200("Delete.schedule.success", {})

    def read_schedule(self, schedule_id):
        schedule_detail = self.session.query(ScanScheduleBase). \
            filter(ScanScheduleBase.id.__eq__(schedule_id)).first()
        account_inform = self.session.query(ScheduleAccountBase).outerjoin(AccountBase). \
            filter(ScheduleAccountBase.schedule_id.__eq__(schedule_id)).all()
        website_inform = self.session.query(ScheduleWebsiteBase).outerjoin(WebsiteBase). \
            filter(ScheduleWebsiteBase.schedule_id.__eq__(schedule_id)).all()
        account = []
        for i in account_inform:
            account_base = {
                "account_id": i.object_account.id if i.object_account is not None else None,
                "account": i.object_account.name if i.object_account is not None else None
            }
            account.append(account_base)
        website = []
        for i in website_inform:
            website_base = {
                "website_id": i.object_website.id if i.object_website is not None else None,
                "website": i.object_website.website_domain if i.object_website is not None else None
            }
            website.append(website_base)
        if schedule_detail:
            schedule_base_data = {
                "id": schedule_detail.id,
                "periods": {
                    "period_id": schedule_detail.object_period.id if schedule_detail.object_period is not None else None,
                    "period": schedule_detail.object_period.period_name if
                    schedule_detail.object_period is not None else None
                },
                "start_in": str(schedule_detail.start_in),
                "mail_senders": {
                    "mail_sender_id": schedule_detail.object_mail_sender.id if
                    schedule_detail.object_mail_sender is not None else None,
                    "mail_sender": schedule_detail.object_mail_sender.email if
                    schedule_detail.object_mail_sender is not None else None
                },
                "accounts": account,
                "websites": website
            }
            return schedule_base_data
        else:
            return {}
