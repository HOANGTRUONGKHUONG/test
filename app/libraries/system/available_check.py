from app.libraries.system.shell import check_open_port
from app.setting import DATABASE_HOST, DATABASE_PORT, CLICKHOUSE_HOST, CLICKHOUSE_PORT


def check_database_available():
    # check Mysql
    mysql = check_open_port(DATABASE_HOST, DATABASE_PORT)
    # check Clickhouse
    clickhouse = check_open_port(CLICKHOUSE_HOST, CLICKHOUSE_PORT)
    print(mysql, clickhouse)
    if mysql['is_open'] and clickhouse['is_open']:
        return True
    return False


def is_interface_operstate_up(interface_name):
    with open(f"/sys/class/net/{interface_name}/operstate", "r") as f:
        status = f.read().rstrip()
    if status == "up":
        return True
    return False
