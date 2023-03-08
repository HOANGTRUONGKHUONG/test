import smtplib
import ssl

from app.libraries.logger import c_logger
from app.setting import MONITOR_LOG_DIR

logger = c_logger(MONITOR_LOG_DIR + "/send_mail_helper.log")


def get_email_provider_information(provider_name):
    # default value
    smtp_server_name = 'smtp.gmail.com'
    smtp_port = 587
    if provider_name == 'gmail':
        smtp_server_name = 'smtp.gmail.com'
    elif provider_name == 'yahoo':
        smtp_server_name = 'smtp.mail.yahoo.com'
    elif provider_name == 'outlook':
        smtp_server_name = 'smtp-mail.outlook.com'
    return {'server_name': smtp_server_name, 'server_port': smtp_port}


def send_email(email_provider, sender_information, receiver_list, mime_message):
    smtp_server_information = get_email_provider_information(email_provider)
    context = ssl.create_default_context()
    mime_message['To'] = ", ".join(receiver_list)
    mime_message['From'] = sender_information['email']
    if smtp_server_information['server_port'] == 587:
        mail_server = smtplib.SMTP(smtp_server_information['server_name'], smtp_server_information['server_port'])
        mail_server.starttls(context=context)
    else:
        # port = 465
        mail_server = smtplib.SMTP_SSL(smtp_server_information['server_name'], smtp_server_information['server_port'],
                                       context=context)
    try:
        mail_server.login(sender_information['email'], sender_information['password'])
        mail_server.sendmail(sender_information['email'], receiver_list, mime_message.as_string())
    except Exception as e:
        print(f"Error {e}")
        return False
    finally:
        mail_server.quit()
    return True
