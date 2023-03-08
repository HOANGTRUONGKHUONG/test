import datetime

from sqlalchemy import or_, and_

from app.libraries.data_format.paging import verify_paging_parameters
from app.libraries.system.sys_time import string_to_datetime


def verify_http_datetime_parameter(logger, http_parameters):
    if "dateType" in http_parameters:
        # http has datetime parameters
        if http_parameters["dateType"] not in ["second", "minute", "hour", "day", "month", "between"]:
            logger.error(f"dateType {http_parameters['dateType']} not validate")
            return f"dateType {http_parameters['dateType']} not validate"
        if http_parameters["dateType"] != "between":
            # dateType in ["second", "minute", "hour", "day", "month"]
            # with dateType in list, param must have dateValue to know query time
            if "dateValue" not in http_parameters:
                logger.error(f"dateValue missing")
                # missing dateValue
                return f"{http_parameters['dateType']} => dateValue missing"
        else:
            # between
            if "dateFrom" not in http_parameters or "dateTo" not in http_parameters:
                # missing dateFrom and dateTo
                logger.error(f"dateFrom and dateTo missing")
                return "between => dateFrom and dateTo missing"
        return ""
    else:
        return "dateType missing"


def filter_datetime(http_parameters, logger, list_id, base):
    filter_error = verify_http_datetime_parameter(logger, http_parameters)
    if filter_error != "":
        logger.error(f"http parameter datetime filter {filter_error}")
        return list_id
    date_type = http_parameters["dateType"]
    if date_type == "second":
        filter_time = datetime.datetime.now() - datetime.timedelta(seconds=float(http_parameters["dateValue"]))
        list_id = list_id.filter(base.datetime >= filter_time)
    elif date_type == "minute":
        filter_time = datetime.datetime.now() - datetime.timedelta(minutes=float(http_parameters["dateValue"]))
        list_id = list_id.filter(base.datetime >= filter_time)
    elif date_type == "hour":
        filter_time = datetime.datetime.now() - datetime.timedelta(hours=float(http_parameters["dateValue"]))
        list_id = list_id.filter(base.datetime >= filter_time)
    elif date_type == "day":
        filter_time = datetime.datetime.now() - datetime.timedelta(days=float(http_parameters["dateValue"]))
        list_id = list_id.filter(base.datetime >= filter_time)
    elif date_type == "month":
        filter_time = datetime.datetime.now() - datetime.timedelta(
            days=float(http_parameters["dateValue"]) * 365 / 12)
        list_id = list_id.filter(base.datetime >= filter_time)
    else:
        # date_type == "between":
        list_id = list_id.filter(
            and_(base.datetime >= string_to_datetime(http_parameters["dateFrom"]),
                 base.datetime <= string_to_datetime(http_parameters["dateTo"]))
        )
    return list_id


def get_list_filter_value(http_parameters):
    list_filter_value = []
    except_param = ["orderType", "orderBy", "dateType", "dateFrom", "dateTo", "dateValue", "limit", "offset", "search"]
    for filter_param in http_parameters:
        if filter_param not in except_param:
            list_filter_value.append(filter_param)
    return list_filter_value


def advanced_filter(http_parameters, logger, list_id, base):
    list_filter_value = get_list_filter_value(http_parameters)
    for item in list_filter_value:
        try:
            column = base.__table__.columns[item]
            if http_parameters[item][0] == "!":
                list_id = list_id.filter(column.notlike(f"%{http_parameters[item][1:]}%"))
            else:
                list_id = list_id.filter(column.like(f"%{http_parameters[item]}%"))
        except Exception as e:
            logger.error(f"Param error {e}")
    return list_id


# return default value off request include limit, offset, order
def get_default_value(logger, http_parameters, base):
    paging_error = verify_paging_parameters(http_parameters)
    order_default = base.__table__.columns["id"].asc()
    if paging_error != "":
        logger.error(f"Paging error, {paging_error}")
        # return default limit offset and order
        return 10, 0, order_default
    limit, offset = int(http_parameters["limit"]), int(http_parameters["offset"])

    try:
        order = base.__table__.columns[http_parameters["orderBy"]]
        order = order.desc() if http_parameters["orderType"] == "desc" else order.asc()
    except Exception as e:
        raise e
        logger.error(f"Order by {e} error, {http_parameters}")
        # return request limit offset and default order
        return limit, offset, order_default
    return limit, offset, order


# return list id with search in http pm
def get_search_value(http_parameters, logger, list_id, base):
    if "search" in http_parameters:
        search_string = http_parameters["search"]
        list_id = list_id.filter(
            or_(key.like(f"%{search_string}%") for key in base.__table__.columns)
        )
    else:
        logger.debug(f"Search is missing")
    return list_id


# return list_id and number of result in total with query
# only use when object in single table
def get_id_single_table(session, logger, http_parameters, base):
    print ("HTTP PARAM: ", http_parameters)
    limit, offset, order = get_default_value(logger, http_parameters, base)
    list_id = session.query(base)
    # advance filter result
    # datetime filter
    list_id = filter_datetime(http_parameters, logger, list_id, base)
    # value filter
    list_id = advanced_filter(http_parameters, logger, list_id, base)
    # optional parameter
    list_id = get_search_value(http_parameters, logger, list_id, base)

    # group result
    list_id = list_id.group_by(base.id).order_by(order)
    # get final result
    number_of_value = list_id.count()
    # limit number of value
    if "avg_value" in http_parameters:
        list_id = list_id
    else:
        list_id = list_id.limit(limit).offset(offset)

    list_id = list_id.all()
    return list_id, number_of_value




