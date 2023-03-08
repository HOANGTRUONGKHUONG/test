import datetime
import re

import validators


def is_port(port_number):
    try:
        if port_number.isdigit() and 1 <= int(port_number) <= 65535:
            return True
        return False
    except Exception as e:
        print(e)
        return False


def is_domain(domain):
    try:
        if validators.domain(domain):
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def is_ipv4(ip_address):
    try:
        if validators.ipv4(ip_address):
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def is_ipv6(ip_address):
    try:
        if validators.ipv6(ip_address):
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def is_mac_address(mac_address):
    try:
        if validators.mac_address(mac_address):
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def is_url(url):
    try:
        if validators.url(url):
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def is_true_datetime_format(date_time):
    try:
        datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False


def is_ipv4_subnet(subnet):
    if 0 <= int(subnet) <= 32:
        return True
    else:
        return False


def is_ipv6_subnet(subnet):
    if 0 <= int(subnet) <= 128:
        return True
    else:
        return False


def is_email(email):
    check_email = r"^[a-z][a-z0-9_\.]{4,32}@[a-z0-9]{2,}(\.[a-z0-9]{2,4}){1,2}$"
    check_email_result = re.finditer(check_email, email)
    if check_email_result:
        return True
    else:
        return False


def is_password(password):
    check_password = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
    check_password_result = re.search(check_password, password)
    if check_password_result:
        return True
    else:
        return False


def is_right_datetime(date_time):
    try:
        datetime.datetime.strptime(date_time, '%d/%m/%Y')
        return True
    except ValueError:
        return False


def is_datetime_right(date_time):
    try:
        datetime.datetime.strptime(date_time, '%Y-%m-%d')
        return True
    except ValueError:
        return False
