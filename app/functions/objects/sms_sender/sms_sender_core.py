from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import *
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.model import SMSSenderBase


class SMSSender(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("object_sms_sender")

    def get_all_sms_sender(self, http_parameters):
        list_sender_id, number_of_sms_sender = get_id_single_table(self.session, self.logger.log_writer, http_parameters,
                                                                   SMSSenderBase)

        all_sms_sender_base_data = []
        for sender in list_sender_id:
            all_sms_sender_base_data.append(self.read_mail_sms_detail(sender.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(reformat_data_with_paging(
            all_sms_sender_base_data, number_of_sms_sender, http_parameters["limit"], http_parameters["offset"]
        ))

    def read_mail_sms_detail(self, sms_id):
        sms_sender_detail = self.session.query(SMSSenderBase).filter(SMSSenderBase.id.__eq__(sms_id)).first()
        if sms_sender_detail:
            mail_sender_base_data = {
                "id": sms_sender_detail.id,
                "name": sms_sender_detail.sms_sender_name,
            }
            return mail_sender_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            self.logger.log_writer.error(f"Query sms sender detail error", {sms_sender_detail})
            return {}
