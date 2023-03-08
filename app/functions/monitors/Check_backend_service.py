from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.functions.monitors.traffic.bandwidth_alert_service import get_mail_sender, get_mail_receiver
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.inout.send_mail_helper import send_email
from app.libraries.system.shell import check_open_port
from app.model import WebsiteUpstreamBase, WebsiteBase

session, engine_connect = ORMSession_alter()


def export_list_data():
	list_data = []
	items = session.query(WebsiteUpstreamBase).outerjoin(WebsiteBase).all()
	for item in items:
		data = {
			"website_name": item.object_website.website_domain if item.object_website is not None else None,
			"website_ip": item.upstream_ip,
			"website_port": item.upstream_port
		}
		list_data.append(data)
		session.close()
		engine_connect.dispose()
	return list_data


if __name__ == '__main__':
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Alert BIF Team Server"
	list_data = export_list_data()
	mail_sender = get_mail_sender(4)
	receiver_list = get_mail_receiver()
	mine_message = ""
	for data in list_data:
		response = check_open_port(data["website_ip"], data["website_port"])
		if response["is_open"] == 0:
			mine_message = mine_message + f"Website {data['website_name']} is not responding \n"
	msg.attach(MIMEText(mine_message, 'plain', 'utf-8'))
	if mine_message == "":
		print("No event")
	else:
		status = send_email('gmail', mail_sender, receiver_list, msg)
		print(status)
