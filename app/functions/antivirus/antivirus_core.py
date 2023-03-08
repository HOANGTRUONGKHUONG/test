# from curses.ascii import BS
from flask import send_file
from email.mime import base
from app.model.ClickhouseModel import MonitorFileScanned
from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.logger import c_logger
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.paging import *
from app.libraries.http.response import *
from app.libraries.data_format.clickhouse_helper import get_data_table
import os
#test
#FILE_PATH = "/usr/local/openresty/nginx/conf.d"
#reality
FILE_PATH = "/var/tmp/upload"

class AntivirusCore(object):
    def __init__(self):
        self.session,self.engine_connect = ORMSession_alter()
        self.logger = c_logger("test").log_writer
        self.db = ClickhouseBase()
        try:
            self.list_file = os.listdir(FILE_PATH)
        except Exception:
            os.mkdir(FILE_PATH)
    
    def extract_value(self, list_item):
        _all_base_data = []
        for item in list_item:
            base_item = item.to_dict()
            if base_item["message"]=="Warning":
                data = {
                "filename":base_item["filename"],
                "source_ip":base_item["source_ip"],
                "group_website":base_item["group_website"],
                "website":base_item["website"],
                "url":base_item["url"],
                "datetime":base_item["datetime"],
                "detect_status":"Suspected"
            }
                _all_base_data.append(data)
            elif base_item["message"]=="Access denied with code 403 (phase 2)":
                data = {
                "filename":base_item["filename"],
                "source_ip":base_item["source_ip"],
                "group_website":base_item["group_website"],
                "website":base_item["website"],
                "url":base_item["url"],
                "datetime":base_item["datetime"],
                "detect_status":"Detected"
            }
                _all_base_data.append(data)
        return _all_base_data

    def get_all_file_scanned(self,http_parameters):

        list_item, number_of_value = get_data_table(self.db ,self.logger, http_parameters, MonitorFileScanned)
        # list_item = MonitorFileUpload.objects_in(self.db)
        if "avg_value" in http_parameters:
            all_base_data = get_average_data(self.extract_value(list_item), http_parameters["avg_value"],
                                             self.list_param)
            http_parameters["limit"] = http_parameters["avg_value"]
            number_of_value = len(all_base_data)
        else:
            all_base_data = self.extract_value(list_item)
            
        if "search" in http_parameters:
            result = []
            for record in all_base_data:
                for key in record:
                    if http_parameters['search'] in str(record[key]) and (record not in result):
                        result.append(record)
                        continue            
            return get_status_code_200(
                reformat_data_with_paging(result, len(result),
                                      int(http_parameters["limit"]), int(http_parameters["offset"]))
            )
        else:
            return get_status_code_200(
                reformat_data_with_paging(all_base_data, number_of_value,
                                      int(http_parameters["limit"]), int(http_parameters["offset"]))
            )
    def download_file_scanned(self,file_name):
        try:
            if file_name in self.list_file:
                # monitor_setting = log_setting("Backup", 1, "Download backup file")
                return send_file(f"{FILE_PATH}/{file_name}", mimetype='application/text',
                                 as_attachment=True, conditional=True)
            else:
                return  status_code_400(f"Information incorrect")
        except Exception as e:
            return status_code_400(e)
