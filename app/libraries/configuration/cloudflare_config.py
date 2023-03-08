import json
import os
import CloudFlare
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("CLOUDFLARE_TOKEN")
application_zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
CLOUDFLARE_API_URL = "https://api.cloudflare.com/client/v4"


def is_using_cloudflare_proxy():
    _cf = CloudFlare.CloudFlare(token=token)
    # get dns records
    dns_records = _cf.zones.dns_records.get(application_zone_id, params={'per_page': 200})
    # check record enabled proxy
    if any(d['proxied'] is True for d in dns_records) is True:
        return True
    else:
        return False


def list_access_rule(_token=token, _application_zone_id=application_zone_id):
    url = f"{CLOUDFLARE_API_URL}/zones/{_application_zone_id}/firewall/access_rules/rules?per_page=1000"
    headers = {
        'Authorization': f'Bearer {_token}'
    }
    response = requests.request("GET", url, headers=headers)
    return json.loads(response.text)


# payload = {
#         "mode": "block",
#         "configuration": {
#             "target": "ip",
#             "value": "1.1.1.1"
#         },
#         "notes": "Sync from BWAF"
#     }
def create_access_rule(_payload, _token=token,
                       _application_zone_id=application_zone_id):
    url = f"{CLOUDFLARE_API_URL}/zones/{_application_zone_id}/firewall/access_rules/rules"
    headers = {
        'Authorization': f'Bearer {_token}',
        'Content-Type': 'application/json',
    }
    response = requests.request("POST", url, headers=headers, data=json.dumps(_payload))
    return json.loads(response.text)


def delete_access_rule(identifier, _token=token, _application_zone_id=application_zone_id):
    url = f"{CLOUDFLARE_API_URL}/zones/{_application_zone_id}/firewall/access_rules/rules/{identifier}"
    headers = {
        'Authorization': f'Bearer {_token}',
        'Content-Type': 'application/json',
    }
    response = requests.request("DELETE", url, headers=headers)
    return json.loads(response.text)


def get_dns_rednscord_id(_token=token, _application_zone_id=application_zone_id, domain=None, ip=None, option=None):
    _cf = CloudFlare.CloudFlare(token=_token)
    params = {}
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
            'content': record['content'],
            'ttl': record['ttl']
        }
        if option == "on":
            update_data.update({"proxied": True})
        elif option == "off":
            update_data.update({"proxied": False})
        record_change_response = _cf.zones.dns_records.put(_application_zone_id, record['id'], data=update_data)
    else:
        return "no domain data"
    return record_change_response


def load_balancers_cloudflare_proxy(_token=token, _application_zone_id=application_zone_id, option=None):
    _cf = CloudFlare.CloudFlare(token=token)
    params = {}
    # get load_balancers records
    load_balancers_records = _cf.zones.load_balancers.get(application_zone_id, params=params)
    # check record enabled proxy
    for domain in load_balancers_records:
        if domain and domain['name'] == "whitehat.vn":
            if option == "on":
                domain.update({"proxied": True})
            elif option == "off":
                domain.update({"proxied": False})
            new_response = _cf.zones.load_balancers.put(_application_zone_id, domain['id'], data=domain)
        else:
            return "no domain data"
        return new_response


def get_load_balancers_cloudflare(_token=token, _application_zone_id=application_zone_id):
    _cf = CloudFlare.CloudFlare(token=token)
    params = {}
    # get load_balancers records
    status = False
    load_balancers_records = _cf.zones.load_balancers.get(application_zone_id, params=params)
    for domain in load_balancers_records:
        if domain and domain['name'] == "whitehat.vn":
            status = domain['proxied']
        else:
            return "no domain data"
    # check record enabled proxy
    return status


def get_zone(_token=token, _application_zone_id=application_zone_id):
    _cf = CloudFlare.CloudFlare(token=_token)
    zone_infor = _cf.zones.get(_application_zone_id)
    return zone_infor
