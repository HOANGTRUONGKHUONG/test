import time

from app.libraries.configuration.firewall import run_config_rule
from app.libraries.system.available_check import check_database_available
from app.libraries.system.shell import run_command

while not check_database_available():
    print("Database not available yet")
    time.sleep(1)

# start some service

# config iptables from database
run_config_rule()

# config network if need

# run custom bash after reboot: route, iptables
# if want to run some bash after reboot, copy app/functions/power_init/power_init.sh.example to /root directory
# and rename to power_init.sh, chmod +x /root/power_init.sh
run_command('')
