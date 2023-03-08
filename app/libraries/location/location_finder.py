from geolite2 import geolite2


def find_country(ip_address):
    try:
        result = geolite2.reader().get(ip_address)
        response = result['country']['iso_code']
    except Exception as e:
        print(e)
        response = "Other"
    return response
