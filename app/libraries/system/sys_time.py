import datetime

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_current_time():
    return datetime.datetime.now().strftime(DATETIME_FORMAT)


def datetime_to_str(input_datetime):
    if input_datetime:
        return input_datetime.strftime(DATETIME_FORMAT)
    return None


def timestamp_to_str(timestamp):
    if timestamp:
        return datetime_to_str(datetime.datetime.fromtimestamp(timestamp))
    return None


def string_to_datetime(time_string):
    datetime_obj = datetime.datetime.strptime(time_string, DATETIME_FORMAT)
    return datetime_obj
