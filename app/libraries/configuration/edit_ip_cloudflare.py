from app.libraries.configuration.cloudflare_config import get_dns_rednscord_id
import os
import time

import CloudFlare

application_zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
token = os.getenv("CLOUDFLARE_TOKEN")


def put_dns_rednscord_edit_id(_token=token, _application_zone_id=application_zone_id, domain=None, ip=None):
    _cf = CloudFlare.CloudFlare(token=_token)
    params = {}
    # Dai ip maf domai do dang co
    list_ip = ["123.30.245.55", "123.30.245.48"]
    list_ip.remove(ip)

    if domain is not None:
        params.update({"name": domain})
        if ip is not None:
            params.update({'content': ip})
    elif ip is not None:
        params.update({'content': ip})
    record_data = _cf.zones.dns_records.get(application_zone_id, params=params)
    if record_data:
        record = record_data[0]
        update_data = {
            'type': record['type'],
            'name': record['name'],
            'proxied': record['proxied'],
            'ttl': record['ttl']
        }
        if record['proxied']:
            for new_ip in list_ip:
                update_data.update({"content": new_ip})
        record_change_response = _cf.zones.dns_records.put(_application_zone_id, record['id'], data=update_data)
    else:
        return "no domain data"
    return record_change_response


def run():
    # Get ip hien tai tren cloudfare
    proxi = get_dns_rednscord_id(token, application_zone_id, "test.whitehat.vn")
    ip_start = proxi["content"]
    print("ip_start:", ip_start)
    # Bat proxi
    get_dns_rednscord_id(token, application_zone_id, "test.whitehat.vn", ip_start, "on")
    time.sleep(60)
    # Chuyen doi sang ip khac
    put_dns_rednscord_edit_id(token, application_zone_id, "test.whitehat.vn", ip_start)


run()
