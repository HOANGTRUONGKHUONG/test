import datetime

from app.libraries.ORMBase import ORMSession_alter
from app.libraries.http.response import status_code_400
from app.libraries.inout.file import read_json_file, write_json_file
from app.model import ScheduleWebsiteBase, ScanScheduleBase

session, engine_connect = ORMSession_alter()
DATA_FROM = "/home/bwaf/bwaf/scans_queue.json"


def create_session(schedule_id):
    try:
        queue = read_json_file(DATA_FROM)
    except Exception as e:
        queue = []
    website = session.query(ScheduleWebsiteBase).all()
    for i in website:
        if i.schedule_id == schedule_id:
            scan_data = {
                "url": i.object_website.website_domain if i.object_website is not None else None,
                "vulnerability": 4,
                "type": "schedule"
            }
            queue.append(scan_data)

            if len(queue) > 100:
                return status_code_400("queue is full, waiting")
    write_json_file(DATA_FROM, queue)


list_schedule = session.query(ScanScheduleBase).all()
today = datetime.datetime.today()
for i in list_schedule:
    period = i.object_period.period_name if i.object_period is not None else None
    if period == "Daily":
        create_session(i.id)
    if period == "Weekly":
        if today.weekday() == 0:
            create_session(i.id)
    if period == "Yearly":
        if today.day == 1 and today.month == 1:
            create_session(i.id)
    if period == "Monthly":
        if today.day == 1:
            create_session(i.id)
session.close()
engine_connect.dispose()