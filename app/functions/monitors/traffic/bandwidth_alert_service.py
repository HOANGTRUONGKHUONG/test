import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.configuration.network import read_interface_information
from app.libraries.inout.send_mail_helper import send_email
from app.model import MailSenderBase, AccountBase
from app.model.ClickhouseModel import MonitorTraffic as MonitorTrafficBase

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
db = ClickhouseBase()
session, engine_connect = ORMSession_alter()


def get_mail_sender(sender_id):
	mail_sender_item = session.query(MailSenderBase). \
		filter(MailSenderBase.id.__eq__(sender_id)).first()
	if mail_sender_item:
		mail_sender_base_data = {
			"email": mail_sender_item.email,
			"password": mail_sender_item.password,
		}
		return mail_sender_base_data
	else:
		session.close()
		engine_connect.dispose()
		return {}
		



def get_mail_receiver():
	mail_receiver = session.query(AccountBase).all()
	account = []
	for i in mail_receiver:
		account.append(i.email)
	return account


if __name__ == '__main__':
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Alert BIF Team Server"
	list_item = MonitorTrafficBase.objects_in(db).only("input", "datetime"). \
		filter(MonitorTrafficBase.interface_id.__eq__(1)).order_by("-datetime")
	ip = read_interface_information("eno1")["ipv4"][0]["addr"]
	mail_sender = get_mail_sender(4)
	receiver_list = get_mail_receiver()
	mine_message = f"Your server is Down - This message is sent from WAF {ip} - and bandwidth is {list_item[0].input}"
	msg.attach(MIMEText(mine_message, 'plain', 'utf-8'))
	if list_item[0].input > 150000000:
		status = send_email('gmail', mail_sender, receiver_list, msg)
		print(status)
