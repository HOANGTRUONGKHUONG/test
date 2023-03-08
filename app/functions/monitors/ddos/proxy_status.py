import os

from app.libraries.configuration.aws_waf_config import is_using_aws_proxy
from app.libraries.configuration.cloudflare_config import is_using_cloudflare_proxy


def is_using_proxy():
    if is_using_cloudflare_proxy() or is_using_aws_proxy():
        return True
    return False


if __name__ == '__main__':
    proxy_status = is_using_proxy()
    if proxy_status:
        print("Proxy enable")
        # check program start or not, if not start program
        st = os.popen("ps ax | grep -v grep | grep \"proxy_config\" | wc -l").read().replace("\n", "")
        if int(st) == 0:
            # run program
            print("Program not running")
            os.popen(
                "/usr/bin/python3 /home/bwaf/bwaf/app/functions/monitors/ddos/proxy_config.py > /dev/null 2>&1 &")
        else:
            # keep running
            print("Program is running")
            pass
    else:
        # check program running or not, if running kill program
        print("Proxy disable")
        output = os.popen("sudo ps axf | grep proxy_config | grep -v grep | awk '{print \"kill -9 \" $1}' | sh")
