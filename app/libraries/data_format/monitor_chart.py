from datetime import datetime, timedelta

from infi.clickhouse_orm import F

from app.libraries.data_format.clickhouse_helper import filter_datetime


def group_data_by_hour(db, base):
    filter_time = datetime.utcnow() - timedelta(days=1)
    list_item = base.objects_in(db).filter(base.datetime >= filter_time). \
        aggregate(hour=F.toHour(base.datetime), num=F.count())
    list_item = list_item.group_by('hour')
    base_data = []
    raw_data = {}
    for item in list(range(0, 24)):
        raw_data[item] = 0
    for item in list_item:
        _item = item.to_dict()
        raw_data[_item['hour']] = _item['num']

    for i in range(0, 24):
        data = {
            "key": i,
            "value": raw_data[i]
        }
        base_data.append(data)
    return base_data


def get_monitor_data_chart(db, base, column, http_parameters, logger):
    list_item = base.objects_in(db)
    list_item = filter_datetime(http_parameters, logger, list_item, base)
    list_item = list_item.aggregate(base().get_field(column), num=F.count())
    list_item = list_item.order_by('-num').paginate(page_num=1, page_size=int(http_parameters[column])).objects
    base_data = []
    for item in list_item:
        _item = item.to_dict()
        data = {
            "key": _item[column],
            "value": _item['num']
        }
        base_data.append(data)
    return base_data




