import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.change_data import filter_time, export_data, export_scan_data
from app.libraries.data_format.chart_maker import export_bar_chart, export_pie_chart
from app.libraries.inout.send_mail_helper import send_email
from app.libraries.logger import c_logger
from app.model import ReportBase, MailSenderBase, PeriodBase, ReportAccountBase, AccountBase, MailServerBase, \
    ScanHistoryBase, ScanResultDetailBase
from app.model.ClickhouseModel import MonitorDdosApplication, MonitorWAF
from app.setting import MONITOR_LOG_DIR

DATETIME_FORMAT = '%H:%M:%S %Y-%m-%d'


# replace one line
def replace_value(html, string1, string2, replace_string):
    start = html.find(string1)
    end = html.find(string2, start)
    target = html[start:end]
    return html.replace(target, string1 + replace_string)


# replace all value
def reformat_email_template(html, period, report_data):
    db = ClickhouseBase()
    date_format = '%d-%m-%Y'
    # base on period value in database
    filter_time_data = filter_time(period)
    period_time = f"Bkav WAF: {filter_time_data['begin'].strftime(date_format)} -" \
                  f" {filter_time_data['end'].strftime(date_format)}"
    html = replace_value(html, "id='PeriodTime'>", "</p>", period_time)
    # base on datetime now
    create_time = f"The report was generated automatically by Bkav WAF at " \
                  f"{datetime.datetime.now().strftime(DATETIME_FORMAT)}"
    html = replace_value(html, "id='CreateTime'>", "</p>", create_time)
    # replace total value
    number_of_ddos_event = str(report_data["ddos_website"]["total_number"])
    number_of_waf_event = str(report_data["waf_website"]["total_number"])
    number_of_vulnerable = str(report_data["san_total_vulner"]["total_top"])
    html = replace_value(html, "id='DDosValue'>", "</td>", number_of_ddos_event)
    html = replace_value(html, "id='WafValue'>", "</td>", number_of_waf_event)
    html = replace_value(html, "id='ScanValue'>", "</td>", number_of_vulnerable)
    # replace chart value
    html = replace_value(html, "id='DDoSChart'>", "</p>", "<img src='cid:ddos_chart'>")
    html = replace_value(html, "id='WafChart'>", "</p>", "<img src='cid:waf_chart'>")
    html = replace_value(html, "id='WafBar'>", "</p>", "<img src='cid:waf_bar'>")
    html = replace_value(html, "id='ScanChart'>", "</p>", "<img src='cid:scan_chart'>")
    html = replace_value(html, "id='ScanBar'>", "</p>", "<img src='cid:scan_bar'>")
    # replace datatable value
    html = replace_value(html, "id='DDoSTable'>", "</table>", create_datatable(report_data['ddos_website']))
    html = replace_value(html, "id='WafTable'>", "</table>", create_datatable(report_data['waf_website']))
    html = replace_value(html, "id='ScanTable'>", "</table>", create_datatable(report_data['san_total_vulner']))
    return html


# table html code only
def create_datatable(table_data):
    # create table header
    html_table = """<table id="t01"><tr><th>Website</th><th>Events</th></tr>"""
    # for data in table_data['raw_data']:
    for data in table_data['raw_data']:
        if type(data) == tuple:
            html_row = "<tr>"
            html_row += f"<td>{str(data[0])}</td>"
            html_row += f"<td>{str(data[1])}</td>"
            html_row += "</tr>"
            html_table += html_row
        else:
            data_obj = data.to_dict()
            html_row = "<tr>"
            for item in data_obj:
                html_row += f"<td>{data_obj[item]}</td>"
            html_row += "</tr>"
            html_table += html_row
    return html_table


def create_image_chart(image_data, image_type, image_id, chart_type, chart_name):
    creator = None
    if chart_type == "bar":
        creator = export_bar_chart(image_data["data"], image_data["ingredients"], image_data["total_top"], chart_name)
    elif chart_type == "pie":
        creator = export_pie_chart(image_data["data"], image_data["ingredients"], chart_name)
    creator.seek(0)
    image_creator = MIMEBase('image', 'jpeg', filename=f'{image_type}.png')
    image_creator.add_header('Content-Disposition', 'attachment', filename=f'{image_type}.png')
    image_creator.add_header('X-Attachment-Id', f'{image_id}')
    if chart_type == "bar":
        image_creator.add_header('Content-ID', f'<{image_type}_bar>')
    elif chart_type == 'pie':
        image_creator.add_header('Content-ID', f'<{image_type}_chart>')
    image_creator.set_payload(creator.read())
    encoders.encode_base64(image_creator)
    return image_creator


def attach_image_chart_to_report(msg, report_data):
    # DDoS country
    msg.attach(create_image_chart(report_data['ddos_country'], "ddos", 1, "pie", "Attacker Country"))
    # WAF country
    msg.attach(create_image_chart(report_data['waf_country'], "waf", 2, "pie", "Attacker Country"))
    # WAF rule
    msg.attach(create_image_chart(report_data['waf_rule'], "waf", 3, "bar", "Attack Type"))
    # Scan total vulner found
    msg.attach(create_image_chart(report_data['san_total_vulner'], "scan", 4, "pie", "Vulnerability Found"))
    # Scan vulner type
    msg.attach(create_image_chart(report_data['scan_vulner_type'], "scan", 5, "bar", "Vulnerability Type"))
    return True


def prepare_data(period):
    db = ClickhouseBase()
    session,engine_connect = ORMSession_alter()
    ddos_country_data = export_data(MonitorDdosApplication, db, period, 'attacker_country')
    ddos_website_data = export_data(MonitorDdosApplication, db, period, 'website_domain')
    waf_country_data = export_data(MonitorWAF, db, period, 'attacker_country')
    waf_website_data = export_data(MonitorWAF, db, period, 'website_domain')
    waf_rule_data = export_data(MonitorWAF, db, period, 'group_rule')
    san_total_vulner_data = export_scan_data(ScanHistoryBase, session, engine_connect, period)
    scan_vulner_type_data = export_scan_data(ScanResultDetailBase, session, engine_connect, period)
    return {
        'ddos_country': ddos_country_data,
        'ddos_website': ddos_website_data,
        'waf_country': waf_country_data,
        'waf_website': waf_website_data,
        'waf_rule': waf_rule_data,
        'san_total_vulner': san_total_vulner_data,
        'scan_vulner_type': scan_vulner_type_data
    }


def make_report(report_object):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"BWAF {report_object['period']} Report"
    report_data = prepare_data(report_object["period"])
    attach_image_chart_to_report(msg, report_data)
    # Make message data
    html_form = report_object["report_form"]
    html_form = reformat_email_template(html_form, report_object["period"], report_data)
    msg.attach(MIMEText(html_form, 'html', 'utf-8'))
    # Send email
    status = send_email(email_provider=report_object["information"]["provider"],
                        sender_information=report_object["information"]["sender"],
                        receiver_list=report_object["information"]["receiver"],
                        mime_message=msg)
    return status


def read_all_report_object(_session):
    # get one report data
    def read_report_detail(report_id):
      
        report_detail = _session.query(ReportBase).outerjoin(MailSenderBase).outerjoin(PeriodBase). \
            outerjoin(MailServerBase).filter(ReportBase.id.__eq__(report_id)).first()
        if report_detail:
            receiver_accounts = _session.query(ReportAccountBase).outerjoin(AccountBase). \
                filter(ReportAccountBase.object_report_id.__eq__(report_id)).all()
            receiver_list = []
            for account in receiver_accounts:
                receiver_list.append(account.object_account.email if account.object_account is not None else None)
            report_data_base = {
                "id": report_detail.id,
                "name": report_detail.name,
                "state": report_detail.state,
                "period": report_detail.object_period.period_name if report_detail.object_period is not None else None,
                "report_form": report_detail.report_form,
                "information": {
                    "provider": report_detail.object_mail_sender.mail_server.end_point,
                    "sender": {
                        "email": report_detail.object_mail_sender.email
                        if report_detail.object_mail_sender is not None else None,
                        "password": report_detail.object_mail_sender.password
                        if report_detail.object_mail_sender is not None else None
                    },
                    "receiver": receiver_list
                }
            }
            return report_data_base
        else:
            return {}

    # get all report data
    list_report = _session.query(ReportBase).all()
    all_report = []
    for rp in list_report:
        all_report.append(read_report_detail(rp.id))
    return all_report


if __name__ == '__main__':
    _session,engine_connect = ORMSession_alter()
    logger = c_logger(MONITOR_LOG_DIR + "/report_service.log")
    report_objects = read_all_report_object(_session)
    today = datetime.datetime.today()
    for report in report_objects:
        if report["state"] == 1:
            if report["period"] == "Daily":
                make_report(report)
            if report["period"] == "Weekly" and today.weekday() == 0:
                make_report(report)
            if report["period"] == "Monthly" and today.day == 1:
                make_report(report)
            if report["period"] == "Yearly" and (today.day == 1 and today.month == 1):
                make_report(report)
        else:
            pass
            
    _session.close()
    engine_connect.dispose()
    print("DONE")
