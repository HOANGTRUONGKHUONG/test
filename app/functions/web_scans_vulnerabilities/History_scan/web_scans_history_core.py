from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.id_helper import get_id_single_table
from app.libraries.data_format.paging import *
from app.libraries.http.response import *
from app.libraries.logger import c_logger
from app.model import ScanHistoryBase
from app.model import ScanResultDetailBase


class WebHistory(object):
    def __init__(self):
        self.session, self.engine_connect = ORMSession_alter()
        self.logger = c_logger("Webhistory").log_writer

    def get_all_history(self, http_parameters):
        list_history_id, number_of_history = get_id_single_table(self.session, self.logger, http_parameters,
                                                                 ScanHistoryBase)
        all_history_data_base = []
        for item in list_history_id:
            all_history_data_base.append(self.read_one_history(item.id))
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(
            reformat_data_with_paging(
                all_history_data_base, number_of_history, http_parameters["limit"], http_parameters["offset"]
            )
        )

    def get_history_inform(self, history_id):
        history_inform = self.session.query(ScanResultDetailBase.id). \
            filter(ScanResultDetailBase.history_id.__eq__(history_id)).all()
        return_data = []
        for i in history_inform:
            return_data.append(self.read_history_detail(i.id))
        base_data = self.read_one_history(history_id)
        del base_data["result"]
        if base_data["total_vulner"] == 0:
            extend_data = {
                "value": "OK",
                "data": return_data
            }
        else:
            extend_data = {
                "value": "NOT OK",
                "data": return_data
            }
        del base_data["total_vulner"]
        base_data.update({"result": extend_data})
        self.session.close()
        self.engine_connect.dispose()
        return get_status_code_200(base_data)

    def read_one_history(self, history_id):
        one_history = self.session.query(ScanHistoryBase).filter(ScanHistoryBase.id.__eq__(history_id)).first()
        if one_history:
            history_base_data = {
                "id": one_history.id,
                "datetime": str(one_history.datetime),
                "website": one_history.website,
                "status": int(bool(one_history.status)) * 100,
                "total_vulner": one_history.total_vulner,
                "ip_address": one_history.ip,
            }
            if one_history.total_vulner == 0:
                extend = {
                    "result": "OK"
                }
                history_base_data.update(extend)
            else:
                extend = {
                    "result": "NOT OK"
                }
                history_base_data.update(extend)
            return history_base_data
        else:
            self.session.close()
            self.engine_connect.dispose()
            return {}

    def read_history_detail(self, id):
        history_detail = self.session.query(ScanResultDetailBase).filter(
            ScanResultDetailBase.id.__eq__(id)).first()
        if history_detail:
            history_detail_base_data = {
                "id": history_detail.id,
                "vulnerability_name": history_detail.vulnerability_name,
                "description": history_detail.description
            }
            return history_detail_base_data
        self.session.close()
        self.engine_connect.dispose()
        return {}
