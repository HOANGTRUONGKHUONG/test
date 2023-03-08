import subprocess

from app.setting import DEVELOPMENT_ENV


def run_command(cmd_command):
    if DEVELOPMENT_ENV is None:
        process = subprocess.Popen(cmd_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = process.communicate()
        return output
    else:
        with open("/tmp/run_command", "a") as f:
            f.write(f"{cmd_command}\n")
        return "success - dev env"


def check_open_port(ip_address, port_number):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    response = {
        "ip_address": ip_address,
        "port": int(port_number),
        "is_open": 0
    }
    try:
        s.connect((ip_address, int(port_number)))
        response["is_open"] = 1
    except Exception as e:
        print(e)
        response["is_open"] = 0
    finally:
        s.close()
    return response
