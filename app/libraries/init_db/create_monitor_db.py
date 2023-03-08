#!/usr/bin/python3
from app.libraries.ClickhouseORM import ClickhouseBase
from app.model.ClickhouseModel import *

db = ClickhouseBase()
db.create_database()
db.create_table(MonitorConnection)
db.create_table(MonitorDdosApplication)
db.create_table(MonitorDdosNetwork)
db.create_table(MonitorHTTP)
db.create_table(MonitorResource)
db.create_table(MonitorSetting)
db.create_table(MonitorTraffic)
db.create_table(MonitorWAF)
db.create_table(MonitorLogin)
db.create_table(MonitorSiteConnection)
db.create_table(MonitorIPConnection)
db.create_table(MonitorFileScanned)