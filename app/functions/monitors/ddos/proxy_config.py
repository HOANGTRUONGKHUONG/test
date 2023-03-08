import time

from app.libraries.configuration.aws_waf_config import add_ip_to_aws_waf
from app.libraries.configuration.cloudflare_config import create_access_rule
from app.functions.monitors.ddos.monitor_ddos_service import extract_log_information

WHITE_LIST = ['118.70.128.104', '113.160.58.10', '113.190.212.40', '118.70.81.254', '222.252.30.113']


if __name__ == '__main__':
    f = open("/var/log/nginx/error.log", "r")
    f.seek(0, 2)
    old_size = f.tell()
    f.close()

    while True:
        f = open("/var/log/nginx/error.log", "r")
        f.seek(0, 2)
        new_size = f.tell()
        print(new_size)
        if new_size > old_size:
            print("new event")
            extend_size = new_size - old_size
            f.seek(old_size)
            new_log = f.read(extend_size)
            log_line = new_log.split("\n")
            old_size = new_size
            attack_list = extract_log_information(log_line)
            print(attack_list)
            amazon_attacker_list = []
            for attacker in attack_list:
                if attacker not in WHITE_LIST:
                    # push to cloudflare
                    payload = {
                        "mode": "block",
                        "configuration": {
                            "target": "ip",
                            "value": attack_list[attacker]["attacker_ip"]
                        },
                        "notes": f"Sync from BWAF {attack_list[attacker]['datetime']}"
                    }
                    cloud_flare_status = create_access_rule(_payload=payload)
                    print(cloud_flare_status)
                    # prepare list ip for amazon
                    amazon_attacker_list.append(attacker)
                else:
                    print(f"IP {attacker} in WHITELIST")
            # push to aws
            amazon_status = add_ip_to_aws_waf(amazon_attacker_list)
            print(amazon_status)
            f.close()
        elif new_size < old_size:
            print("rotate log")
            old_size = 0
            f.close()
        else:
            print("no new event")
            f.close()
        time.sleep(1)
