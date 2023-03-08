from datetime import datetime, timedelta
from infi.clickhouse_orm import *
import pytz
from tzlocal import get_localzone
from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.data_format.id_helper import verify_http_datetime_parameter, get_list_filter_value
from app.libraries.data_format.paging import verify_paging_parameters
from app.libraries.data_format.validate_data import is_true_datetime_format
from app.libraries.system.sys_time import string_to_datetime


def filter_datetime(http_parameters, logger, list_item, base):
    filter_error = verify_http_datetime_parameter(logger, http_parameters)
    if filter_error != "":
        logger.error(f"http parameter datetime filter {filter_error}")
        return list_item
    date_type = http_parameters["dateType"]
    if date_type == "second":
        filter_time = datetime.utcnow() - timedelta(seconds=float(http_parameters["dateValue"]))
        list_item = list_item.filter(base.datetime >= filter_time)
    elif date_type == "minute":
        filter_time = datetime.utcnow() - timedelta(minutes=float(http_parameters["dateValue"]))
        list_item = list_item.filter(base.datetime >= filter_time)
    elif date_type == "hour":
        filter_time = datetime.utcnow() - timedelta(hours=float(http_parameters["dateValue"]))
        list_item = list_item.filter(base.datetime >= filter_time)
    elif date_type == "day":
        filter_time = datetime.utcnow() - timedelta(days=float(http_parameters["dateValue"]))
        list_item = list_item.filter(base.datetime >= filter_time)
    elif date_type == "month":
        filter_time = datetime.utcnow() - timedelta(
            days=float(http_parameters["dateValue"]) * 365 / 12)
        list_item = list_item.filter(base.datetime >= filter_time)
    else:
        local_timezone = get_localzone()
        from_local = string_to_datetime(http_parameters["dateFrom"])
        from_utc = local_timezone.localize(from_local).astimezone(pytz.utc)
        to_local = string_to_datetime(http_parameters["dateTo"])
        to_utc = local_timezone.localize(to_local).astimezone(pytz.utc)
        # date_type == "between":
        list_item = list_item.filter(base.datetime >= from_utc,
                                     base.datetime <= to_utc)
    return list_item


def get_default_value(logger, http_parameters, base):
    paging_error = verify_paging_parameters(http_parameters)
    order_default = base().get_field('datetime')
    if paging_error != "":
        logger.error(f"Paging error, {paging_error}")
        # return default limit offset and order
        return 10, 0, order_default
    limit, offset = int(http_parameters["limit"]), int(http_parameters["offset"])
    try:
        if http_parameters["orderBy"] == "id":
            http_parameters["orderBy"] = "datetime"
        if http_parameters["orderType"] == "asc":
            order = base().get_field(http_parameters["orderBy"])
        else:
            order = f'-{base().get_field(http_parameters["orderBy"])}'
    except Exception as e:
        logger.error(f"Order by {e} error, {http_parameters}")
        # return request limit offset and default order
        return limit, offset, order_default
    return limit, offset, order


def advanced_filter(http_parameters, logger, list_item, base):
    list_filter_value = get_list_filter_value(http_parameters)
    for item in list_filter_value:
        if item != 'datetime' or (item == 'datetime'
                                  and (is_true_datetime_format(http_parameters['datetime'])
                                       or is_true_datetime_format(http_parameters['datetime'][1:]))):
            try:
                if http_parameters[item][0] == "!":
                    list_item = list_item.filter(base().get_field(item) != http_parameters[item][1:])
                else:
                    list_item = list_item.filter(base().get_field(item) == http_parameters[item])
            except Exception as e:
                logger.error(f"Param error {e}")
        else:
            logger.error(f"Param {item, http_parameters[item]} not validate")
            list_item = list_item
    return list_item

#just for file_scanned
def get_search_value(http_parameters, logger, list_item, base):
    if "search" in http_parameters:
        search_string = http_parameters["search"]
        list_item = list_item.filter(base().filename.like(f'%{search_string}%') | 
                                     base().source_ip.like(f'%{search_string}%')|
                                     base().group_website.like(f'%{search_string}%')|
                                     base().website.like(f'%{search_string}%')|
                                     base().datetime.like(f'%{search_string}%')|
                                     base().url.like(f'%{search_string}%')
                                     ) 
        
        # not finish function
    else:
        logger.debug(f"Search is missing")
    return list_item


def get_data_table(db, logger, http_parameters, base):
    limit, offset, order = get_default_value(logger, http_parameters, base)
    list_item = base.objects_in(db)
    # datetime filter
    list_item = filter_datetime(http_parameters, logger, list_item, base)
    # value filter
    list_item = advanced_filter(http_parameters, logger, list_item, base)
    # optional parameter
    # list_item = get_search_value(http_parameters, logger, list_item, base)
    # group result
    list_item = list_item.order_by(order)
    print(list_item)
    # limit number of value
    if "avg_value" in http_parameters:
        list_item = list_item
        number_of_item = list_item.count()
        print(number_of_item)
    else:
        list_item = list_item.paginate(page_num=(offset / limit) + 1, page_size=limit)
        number_of_item = list_item.number_of_objects
        list_item = list_item.objects           
    
    return list_item, number_of_item
