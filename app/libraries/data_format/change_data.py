import copy
import hashlib
import json
from datetime import datetime, timedelta

import pycountry
from infi.clickhouse_orm import F
from sqlalchemy import and_, func

from app.model import ScanHistoryBase, ScanResultDetailBase

form_data = {
    "input_on": {
        "value": 149,
        "don_vi": "Kbps"
    },
    "input_off": {
        "value": 49,
        "don_vi": "Kbps"
    }
}


def md5(data):
    data = hashlib.md5(data.encode())
    return data.hexdigest()


def filter_time(period):
    today = datetime.today()
    if period == "Daily":
        end = today.replace(hour=0, minute=0, second=0, microsecond=0)
        if today.day == 1:
            if today.month in {1, 3, 5, 7, 8, 10, 12}:
                begin = end.replace(day=31)
            else:
                begin = end.replace(day=30)
        else:
            begin = end.replace(day=end.day - 1)
        time = {
            "begin": begin,
            "end": end
        }
        return time
    if period == "Weekly":
        end = today.replace(hour=0, minute=0, second=0, microsecond=0)
        begin = datetime(today.year, today.month, today.day) - timedelta(days=7)
        begin = begin.replace(hour=0, minute=0, second=0, microsecond=0)
        time = {
            "begin": begin,
            "end": end
        }
        return time
    if period == "Monthly":
        end = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if today.month == 1:
            begin = end.replace(month=12)
        else:
            begin = end.replace(month=end.month - 1)
        time = {
            "begin": begin,
            "end": end
        }
        return time
    if period == "Yearly":
        end = today.replace(day=1, month=1, hour=0, minute=0, second=0, microsecond=0)
        begin = end.replace(year=end.year - 1)
        time = {
            "begin": begin,
            "end": end
        }
        return time


def export_data(base, db, period, group_value):
    data_list = base.objects_in(db)
    filter_time_data = filter_time(period)
    data_list = data_list.filter(base.datetime >= filter_time_data["begin"],
                                 base.datetime <= filter_time_data["end"])
    total_number = data_list.count()
    data_list = data_list.aggregate(base().get_field(group_value), value=F.count())
    data_list = data_list.paginate(1, 10).objects
    data = []
    ingredients = []
    top_total = 0
    # calculate percent
    for item in data_list:
        top_total = top_total + item.value
    if group_value == 'attacker_country':
        for item in data_list:
            item_dict = item.to_dict()
            item_value = (item_dict['value'] / top_total) * 100
            data.append(item_value)
            if item_dict[group_value] != "Other":
                country = pycountry.countries.get(alpha_2=item_dict[group_value])
                ingredients.append(country.name)
            else:
                ingredients.append(item_dict[group_value])
    else:
        for item in data_list:
            item_dict = item.to_dict()
            ingredients.append(item_dict[group_value])
            data.append(item.value)
    result = {
        "total_number": total_number,
        "total_top": top_total,
        "raw_data": data_list,
        "data": data,
        "ingredients": ingredients
    }
    return result


def export_scan_data(base, session, engine_connect, period):
    arrays = []
    array_list = []
    if base == ScanHistoryBase:
        array_list = session.query(ScanHistoryBase.website, ScanHistoryBase.total_vulner)
        arrays = session.query(ScanHistoryBase.website).group_by(ScanHistoryBase.website).all()
        array_list = array_list.filter(and_(ScanHistoryBase.datetime >= filter_time(period)["begin"],
                                            ScanHistoryBase.datetime <= filter_time(period)["end"]))
        array_list = array_list.group_by(ScanHistoryBase.website, ScanHistoryBase.total_vulner).order_by(
            ScanHistoryBase.total_vulner.desc()).all()
    if base == ScanResultDetailBase:
        history_id = session.query(ScanHistoryBase.id)
        history_id = history_id.filter(
            and_(ScanHistoryBase.datetime >= filter_time(period)["begin"],
                 ScanHistoryBase.datetime <= filter_time(period)["end"])).all()
        arrays = session.query(ScanResultDetailBase.vulnerability_name).group_by(
            ScanResultDetailBase.vulnerability_name).all()
        array_list = []
        for id in history_id:
            list_vulner = session. \
                query(ScanResultDetailBase.vulnerability_name, func.count(ScanResultDetailBase.vulnerability_name)). \
                filter(ScanResultDetailBase.history_id.__eq__(id[0])). \
                group_by(ScanResultDetailBase.vulnerability_name). \
                order_by(func.count(ScanResultDetailBase.vulnerability_name).desc()).all()
            array_list = array_list + list_vulner
    result = []
    for param in arrays:
        value = 0
        for array in array_list:
            if param[0] == array[0]:
                value = value + array[1]
        if value != 0:
            element = (param[0], value)
            result.append(element)
    data = []
    ingredients = []
    number = 0
    for i in result[:10]:
        number = number + i[1]
        ingredients.append(i[0])
        data.append(i[1])
    return_data = {
        "total_top": number,
        "raw_data": result[:10],
        "data": data,
        "ingredients": ingredients
    }
    session.close()
    engine_connect.dispose()
    return return_data


# input_data = input_on and input_off
def input_intrface(input_data):
    # data = open("data.txt").read()
    # json_data = json.loads(form_data)
    json_data = copy.deepcopy(form_data)
    data_input = json_data[input_data]['value']
    donvi = json_data[input_data]['don_vi']
    if donvi == 'B':
        data_byte = data_input
    elif donvi == 'Kbps' or donvi == 'kbps':
        data_byte = data_input * 125
    elif donvi == 'Mbps' or donvi == 'mbps':
        data_byte = data_input * 125000
    elif donvi == 'Gbps' or donvi == 'gbps':
        data_byte = data_input * 125000000
    elif donvi == 'Tbps' or donvi == 'tbps':
        data_byte = data_input * 125000000000
    else:
        return "error"
    return data_byte
