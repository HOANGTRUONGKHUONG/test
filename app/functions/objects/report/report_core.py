from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import *
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.model import ReportBase, PeriodBase, MailSenderBase, ReportAccountBase, AccountBase, ReportFormBase


def verify_input(json_data):
    verify = " "
    if len(json_data["name"]) > 500:
        verify += "Report name too long"


class Report(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("report")

    def get_period(self):
        list_period_id = self.session.query(PeriodBase.id).all()
        all_period = []
        for i in list_period_id:
            all_period.append(self.read_period(i.id))

        self.session.close()
        self.engine_connect.dispose() 
        return get_status_code_200(all_period)

    def get_all_report(self, http_parameters):
        list_report_id, number_of_report = get_id_single_table(self.session, self.logger.log_writer, http_parameters, ReportBase)

        all_report_base_data = []
        for report in list_report_id:
            all_report_base_data.append(self.read_report_detail(report.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_report_base_data, number_of_report, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def add_new_report(self, json_data):
        report_obj = ReportBase(name=json_data["name"], state=json_data["state"],
                                report_form=json_data["report_form"], period_id=json_data["period"],
                                mail_sender_id=json_data["mail_sender_id"])
        self.session.add(report_obj)
        self.session.flush()
        try:
            self.session.commit()
        except Exception as e:
            self.logger.log_writer.error(f"add report fail, {e}")
            return status_code_500("post.report.fail.server")
        for i in json_data["account_id"]:
            report_account_obj = ReportAccountBase(object_report_id=report_obj.id, object_account_id=i)
            self.session.add(report_account_obj)
            self.session.flush()
            try:
                self.session.commit()
                monitor_setting = log_setting(action="System report", status=1, description="Add new report")
                return status_code_200("post.report.success", self.read_report_detail(report_obj.id))
            except Exception as e:
                monitor_setting = log_setting(action="System report", status=0, description="Add new report failed")
                self.logger.log_writer.error(f"add report fail, {e}")
            finally:
                self.session.close()
                self.engine_connect.dispose()
        return status_code_500("post.report.fail.server")

    def get_report_detail(self, report_id):
        report_detail = self.read_report_detail(report_id)
        self.session.close()
        self.engine_connect.dispose()
        if bool(report_detail):
            return get_status_code_200(report_detail)
        else:
            return status_code_400("get.report.fail.client")

    def edit_report(self, report_id, json_data):
        report_detail = self.read_report_detail(report_id)
        report_detail.update(json_data)
        report_obj = self.session.query(ReportBase).filter(ReportBase.id.__eq__(report_id)).one()
        report_obj.name = report_detail["name"]
        report_obj.state = report_detail["state"]
        report_obj.report_form = report_detail["report_form"]
        report_obj.period_id = report_detail["period"]
        report_obj.mail_sender_id = report_detail["mail_sender_id"]
        self.session.query(ReportAccountBase).filter(ReportAccountBase.object_report_id.__eq__(report_id)).delete()
        self.session.flush()
        for i in json_data["account_id"]:
            report_account_obj = ReportAccountBase(object_report_id=report_obj.id, object_account_id=i)
            self.session.add(report_account_obj)
        self.session.flush()
        try:
            self.session.commit()
            monitor_setting = log_setting(action="System report", status=1, description="Edit report")
        except Exception as e:
            self.logger.log_writer.error(f"edit report fail, {e}")
            monitor_setting = log_setting(action="System report", status=0, description="Edit report failed")
            return status_code_500("put.report.fail.server")
        finally:
            data = self.read_report_detail(report_id)
            self.session.close()
            self.engine_connect.dispose()
        return status_code_200("put.report.success", data)

    def delete_report(self, report_id):
        check = self.session.query(ReportBase).filter(ReportBase.id.__eq__(report_id)).first()
        if check:
            self.session.query(ReportAccountBase).filter(ReportAccountBase.object_report_id.__eq__(report_id)).delete()
            self.session.query(ReportBase).filter(ReportBase.id.__eq__(report_id)).delete()
            try:
                self.session.commit()
                monitor_setting = log_setting(action="System report", status=1, description="Delete report")
                return status_code_200("delete.report.success", {})
            except Exception as e:
                self.logger.log_writer.error(f"delete report fail, {e}")
                monitor_setting = log_setting(action="System report", status=0, description="Delete report failed")
            finally:
                self.session.close()
                self.engine_connect.dispose()
            return status_code_500("delete.report.fail.server")
        else:
            monitor_setting = log_setting(action="System report", status=0, description="Delete report failed")
            return status_code_400("delete.report.fail.client")

    def read_report_detail(self, report_id):
        report_detail = self.session.query(ReportBase).outerjoin(MailSenderBase).outerjoin(PeriodBase). \
            filter(ReportBase.id.__eq__(report_id)).first()
        account_inform = self.session.query(ReportAccountBase).outerjoin(AccountBase). \
            filter(ReportAccountBase.object_report_id.__eq__(report_id)).all()
        account = []
        account_id = []
        for i in account_inform:
            account.append(i.object_account.name if i.object_account is not None else None)
        if report_detail:
            report_data_base = {
                "id": report_detail.id,
                "name": report_detail.name,
                "state": report_detail.state,
                "report_form": report_detail.report_form,
                "period": report_detail.object_period.period_name if
                report_detail.object_period is not None else None,
                "mail_sender": report_detail.object_mail_sender.email if
                report_detail.object_mail_sender is not None else None,
                "account": account
            }
            return report_data_base
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def read_period(self, period_id):
        period = self.session.query(PeriodBase).filter(PeriodBase.id.__eq__(period_id)).first()
        if period:
            period_base_data = {
                "id": period.id,
                "period_name": period.period_name
            }
            return period_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def get_html_form(self):
        result = self.session.query(ReportFormBase.html_form).all()
        self.session.close()
        self.engine_connect.dispose()
        return result
