import boto3

from app.libraries.data_format.validate_data import is_ipv4

AWS_SERVER_PUBLIC_KEY = "AKIA3BHV2V33H7DH7SEG"
AWS_SERVER_SECRET_KEY = "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"
AWS_BLOCK_IPv4_ID = "e187a41e-ef48-4bbb-91b8-abab2d34de18"
AWS_BLOCK_IPv6_ID = "113d9345-49f8-441a-bf94-1e658f510702"
AWS_SITE_ID = 'E2JUX7FXMGDLJK'
AWS_REGION_NAME = 'us-east-1'
# Create Session
session = boto3.Session(
    region_name=AWS_REGION_NAME,
    aws_access_key_id=AWS_SERVER_PUBLIC_KEY,
    aws_secret_access_key=AWS_SERVER_SECRET_KEY
)
waf_v2 = session.client('wafv2')


def is_using_aws_proxy():
    cloudfront = session.client('cloudfront')
    site_distribution = cloudfront.get_distribution(
        Id=AWS_SITE_ID
    )
    check_param = site_distribution['Distribution']['DistributionConfig']['Enabled']
    if check_param:
        return True
    return False


def get_ip_set_data(ip_type):  # ip_type = ipv4 or ipv6
    ip_set_inform = waf_v2.get_ip_set(
        Name=f'Blacklist_{ip_type}',
        Scope='CLOUDFRONT',
        Id=AWS_BLOCK_IPv4_ID if ip_type == 'ipv4' else AWS_BLOCK_IPv6_ID
    )
    ip_set_data = {
        "lock_token": ip_set_inform['LockToken'],
        "list_ip": ip_set_inform["IPSet"]["Addresses"]
    }
    return ip_set_data


def update_aws_ip_set(ip_set_data, ip_type):  # ip_type = ipv4 or ipv6
    update_ip_set = waf_v2.update_ip_set(
        Name=f'Blacklist_{ip_type}',
        Scope='CLOUDFRONT',
        Id=AWS_BLOCK_IPv4_ID if ip_type == 'ipv4' else AWS_BLOCK_IPv6_ID,
        Description=f'Block attack {ip_type}',
        Addresses=ip_set_data["list_ip"],
        LockToken=ip_set_data["lock_token"]
    )
    return update_ip_set


def add_ip_to_ip_set_data(ip_set_data, ip_address):
    def append_list_ip(ip, array):
        if ip in array:
            return array
        else:
            array.append(ip)
            return array

    if is_ipv4(ip_address):
        ip_set_form = ip_address + "/32"
        append_list_ip(ip_set_form, ip_set_data['list_ip'])
    else:
        ip_set_form = ip_address + "/128"
        append_list_ip(ip_set_form, ip_set_data['list_ip'])
    return ip_set_data


def delete_ip_from_ip_set_data(ip_set_data, ip_address):
    def delete_list_ip(ip, array):
        if ip in array:
            array.remove(ip)
            return array
        else:
            return array

    if is_ipv4(ip_address):
        ip_set_form = ip_address + "/32"
        delete_list_ip(ip_set_form, ip_set_data["list_ip"])
        return ip_set_data
    else:
        ip_set_form = ip_address + "/128"
        delete_list_ip(ip_set_form, ip_set_data["list_ip"])
        return ip_set_data


def add_ip_to_aws_waf(list_ip_address):
    ipv4_set = get_ip_set_data('ipv4')
    ipv6_set = get_ip_set_data('ipv6')
    for ip_address in list_ip_address:
        if is_ipv4(ip_address):
            ipv4_set = add_ip_to_ip_set_data(ipv4_set, ip_address)
        else:
            ipv6_set = add_ip_to_ip_set_data(ipv6_set, ip_address)
    result4 = update_aws_ip_set(ipv4_set, 'ipv4')
    result6 = update_aws_ip_set(ipv6_set, 'ipv6')
    return result4, result6


def create_ip_set(name, ip_type):
    ip_set = waf_v2.create_ip_set(
        Name=name,
        Scope='CLOUDFRONT',
        Description='Sync From BWAF',
        IPAddressVersion='IPV4' if ip_type == 'ipv4' else 'IPV6',
        Addresses=[]
    )
    return ip_set


def check_ip_set_exist():
    list_set = waf_v2.list_ip_sets(
        Scope='CLOUDFRONT',
    )
    ip_v4_set_id = None
    ip_v6_set_id = None
    for ip_set in list_set['IPSets']:
        ip_set_inform = waf_v2.get_ip_set(
            Name=ip_set['Name'],
            Scope='CLOUDFRONT',
            Id=ip_set['Id']
        )
        if 'BWAF' in ip_set_inform['IPSet']['Name']:
            if ip_set_inform['IPSet']['IPAddressVersion'] == 'IPV4':
                ip_v4_set_id = ip_set_inform['IPSet']['Id']
            if ip_set_inform['IPSet']['IPAddressVersion'] == 'IPV6':
                ip_v6_set_id = ip_set_inform['IPSet']['Id']
    return {"ipv4": ip_v4_set_id, "ipv6": ip_v6_set_id}


def get_ip_set_id():
    ip_set_exist = check_ip_set_exist()
    print(ip_set_exist)
    # not exist so create
    if ip_set_exist['ipv4'] is None:
        ipv4 = create_ip_set('BWAF_IPV4', 'ipv4')
        ip_set_exist['ipv4'] = ipv4['Summary']['Id']
    if ip_set_exist['ipv6'] is None:
        ipv6 = create_ip_set('BWAF_IPV6', 'ipv6')
        ip_set_exist['ipv6'] = ipv6['Summary']['Id']
    return ip_set_exist
