# Bkav Web Application Firewall
## VERSION INFO
version: 2.0.0
### Features list
- Feature 1
- Feature 2
## INSTALL MANUAL
 Env requirement:
 - OS: Ubuntu 22.04
 - Python: 3.11
 ### Step1 - Install require lib
 ```
 $ sudo apt-get install libmysqlclient-dev
 $ sudo apt install python3-pip
 ```
### Step 2 - Install api lib
```
$ sudo apt install python3-pip
```
```
$ cd app
$ pip3 install -r requirements.txt
```
### Step 4 - Install clickhouse
```
$ sudo apt-get install apt-transport-https ca-certificates dirmngr
$ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv E0C56BD4
$ echo "deb https://repo.clickhouse.tech/deb/stable/ main/" | sudo tee \ /etc/apt/sources.list.d/clickhouse.list
$ sudo apt-get update
$ sudo apt-get install -y clickhouse-server clickhouse-client
$ sudo service clickhouse-server start
```
### Step 5 - Config clickhouse db
```
$ sudo python3 bwaf/app/libraries/init_db/create_monitor_db.py
$ clickhouse-client --password
```
```
ALTER table system.metric_log MODIFY TTL event_time + INTERVAL 1 DAY;
ALTER table system.query_thread_log MODIFY TTL event_time + INTERVAL 1 DAY;
ALTER table system.query_log MODIFY TTL event_time + INTERVAL 1 DAY;
ALTER table system.trace_log MODIFY TTL event_time + INTERVAL 1 DAY;

ALTER table bwaf.monitor_traffic MODIFY TTL datetime + INTERVAL 1 MONTH;
ALTER table bwaf.monitor_setting MODIFY TTL datetime + INTERVAL 1 MONTH;
ALTER table bwaf.monitor_resource MODIFY TTL datetime + INTERVAL 1 MONTH;
ALTER table bwaf.monitor_login MODIFY TTL datetime + INTERVAL 1 MONTH;
ALTER table bwaf.monitor_connection MODIFY TTL datetime + INTERVAL 1 MONTH;
ALTER table bwaf.monitor_http_status_code MODIFY TTL datetime + INTERVAL 1 MONTH;
ALTER table bwaf.monitor_ddos_application_layer MODIFY TTL datetime + INTERVAL 1 MONTH;
ALTER table bwaf.monitor_waf MODIFY TTL datetime + INTERVAL 1 MONTH;
```
### Add python-path
```
$ cd
$ nano .bashrc
```
Thêm dòng cấu hình 'export PYTHONPATH="${PYTHONPATH}:{''}"'
