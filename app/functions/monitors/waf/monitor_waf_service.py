import base64
import re
import time
from collections import OrderedDict
from datetime import datetime

from app.libraries.ClickhouseORM import ClickhouseBase
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.data_format.string_format import json_to_string
from app.libraries.location.location_finder import find_country
from app.libraries.logger import c_logger
from app.libraries.system.available_check import check_database_available
from app.libraries.system.sys_time import get_current_time
from app.model import WebsiteBase, GroupWebsiteBase
from app.model.ClickhouseModel import MonitorWAF
from app.setting import MONITOR_LOG_DIR

SAVE_WARNING = 1
LOG_FILE_DIR = '/var/log/modsec_audit.log'  # product log
# LOG_FILE_DIR='/home/bwaf/bwaf/app/test.log'
# LOG_FILE_DIR = '/home/thanhptg/Desktop/log/thanhptg/test.log'  # debug log

a_pattern = re.compile(r'^---\w{8,10}---A--$')
z_pattern = re.compile(r'^---\w{8,10}---Z--$')
rule_file = re.compile(r'(?<=\[file\s\").*?(?=\"\])')
tag = re.compile(r'(?<=\[tag\s\").*?(?=\"\])')
msg = re.compile(r'(?<=\[msg\s\").*?(?=\"\])')
matched = re.compile(r'(?<=Matched).*?(?=\[)')
rule_id = re.compile(r'(?<=\[id\s\").*?(?=\"\])')
modsec_message_message_pattern = r'(?<=\ModSecurity:).*?(?=\[)'
modsec_event_types = ['A', 'B', 'C', 'E', 'F', 'H', 'I', 'J', 'K']
LOG_TIMESTAMP_FORMAT = '%d/%b/%Y:%H:%M:%S %z'


def process_log_to_info(singleEntry):
    modsec_dict = OrderedDict()
    a_header = singleEntry[0]
    e_separator = a_header[a_header.find('^---') + 4:a_header.find('---A--')]
    itemNumber = 0
    itemKV = OrderedDict()
    try:
        for item in singleEntry:
            if item.__contains__(e_separator):
                itemKV[item.rstrip()[-3:-2:]] = itemNumber
            itemNumber += 1
        item_keys = list(itemKV.keys())
        itemKVFull = OrderedDict()
        for item_letter in item_keys:
            if item_letter in modsec_event_types:
                i = int(itemKV[item_letter]) + 1
                j = itemKV[item_keys[item_keys.index(item_letter) + 1]]
                itemKVFull[item_letter] = singleEntry[i:j]

        modsec_a = itemKVFull['A'][0]
        modsec_b = itemKVFull['B']
        modsec_f = itemKVFull['F']
        modsec_h = itemKVFull['H']

        modsec_b_headers = dict(map(lambda s: [s[0:s.find(': ')], s[s.find(': ') + 2:]], modsec_b[1:-1]))
        modsec_f_headers = dict(
            map(lambda s: [s, '-'] if len(s.split(': ')) == 1 else [s[0:s.find(': ')], s[s.find(': ') + 2:]],
                modsec_f[1:-1]))

        modsec_h_dict = OrderedDict()
        for elem in modsec_h:
            if elem.startswith('Message:') or elem.startswith('ModSecurity:'):
                if 'messages' not in modsec_h_dict:
                    modsec_h_dict['messages'] = [elem]
                else:
                    modsec_h_dict['messages'].append(elem)
            elif elem.startswith('Apache-Handler:'):
                if 'handlers_messages' not in modsec_h_dict:
                    modsec_h_dict['handlers_messages'] = [elem]
                else:
                    modsec_h_dict['handlers_messages'].append(elem)
            elif elem.startswith('Apache-Error:'):
                if 'error_messages' not in modsec_h_dict:
                    modsec_h_dict['error_messages'] = [elem]
                else:
                    modsec_h_dict['error_messages'].append(elem)
            elif elem.startswith('Producer:'):
                modsec_h_dict['producer'] = elem.split(': ')[1].strip(' .').split('; ')
            elif elem.startswith('Engine-Mode:'):
                modsec_h_dict['Engine-Mode'] = elem.split(': ')[1].strip('"')
            elif elem.startswith('Server:'):
                modsec_h_dict['server'] = elem.split(': ')[1]
            elif elem.startswith('Action: '):
                modsec_h_dict['action'] = {}
                if 'ntercepted' in elem:
                    modsec_h_dict['action']['intercepted'] = True
                    modsec_h_dict['action']['phase'] = int(elem[elem.find('phase') + 6])
                    modsec_h_dict['action']['message'] = modsec_h_dict['messages'][-1].split('.')[1].strip()
            elif elem.startswith('Stopwatch2'):
                modsec_h_dict['stopwatch'] = {}
                for stopw in elem.split(' '):
                    if '=' in stopw:
                        modsec_h_dict['stopwatch'][stopw.split('=')[0]] = int(stopw.split('=')[1].strip(','))
            else:
                pass
        modsec_a_split = modsec_a.split()
        log_time = modsec_a_split[0].replace('[', '') + ' ' + modsec_a_split[1].replace(']', '')
        violation_date = datetime.strptime(log_time, LOG_TIMESTAMP_FORMAT)
        modsec_dict['transaction'] = {
            'time': violation_date,
            'transaction_id': modsec_a_split[2], 'remote_address': modsec_a_split[3],
            'remote_port': modsec_a_split[4], 'local_address': modsec_a_split[5], 'local_port': modsec_a_split[6]}
        if len(modsec_b) > 0:
            modsec_dict['request'] = {'request_line': modsec_b[0], 'headers': modsec_b_headers}
        else:
            modsec_dict['request'] = 'None'

        if len(modsec_f_headers) > 3:
            modsec_dict['response'] = OrderedDict()
            try:
                modsec_dict['response'] = {'protocol': modsec_f[0].split(' ')[0], 'status': modsec_f[0].split(' ')[1],
                                           'status_text': ' '.join(modsec_f[0].split(' ')[2:]),
                                           'headers': modsec_f_headers}
            except Exception as e:
                logger.error(f'Exception at modsec_dict["response"] : {e}')
                modsec_dict['response'] = 'None'
        else:
            modsec_dict['response'] = 'None'
        modsec_dict['audit_data'] = OrderedDict()
        modsec_dict['audit_data'] = modsec_h_dict
    except Exception as e:
        logger.error(f'error found: {e} when processing :{singleEntry}')
        modsec_dict = 'ERROR'

    return modsec_dict


def process_audit_log(last_size):
    try:
        modsec_Table = []
        log_file = open(LOG_FILE_DIR, 'r', encoding='cp437')

        # product code -> read realtime
        log_file.seek(0, 2)
        current_size = log_file.tell()
        if current_size > last_size:
            logger.debug(f"Detect new log {get_current_time()}")
            log_file.seek(last_size)
            block_size = current_size - last_size
            new_log = log_file.read(block_size)
            log_lines = new_log.split("\n")
            # logger.debug(log_lines)
            i = 0
            while i < len(log_lines):
                if a_pattern.search(log_lines[i]):
                    modsec_Entry = [log_lines[i]]
                    for j in range(i, len(log_lines)):
                        if z_pattern.search(log_lines[j]):
                            modsec_Entry.append(log_lines[j].rstrip())
                            modsec_Table.append(modsec_Entry)
                            i = j + 1
                            break
                        else:
                            modsec_Entry.append(log_lines[j].rstrip())
                i += 1

            last_size = current_size
            log_file.close()
            return modsec_Table, last_size
        elif current_size < last_size:
            logger.debug(f"Reset log")
            last_size = 0
            log_file.close()
            return modsec_Table, last_size
        else:
            logger.debug("No new log entry")
            log_file.close()
            return modsec_Table, current_size
        # end product code

        # # debug code -> read from file not realtime
        # log_lines = log_file.read().split("\n")
        # i = 0
        # while i < len(log_lines):
        #     if a_pattern.search(log_lines[i]):
        #         modsec_Entry = [log_lines[i]]
        #         for j in range(i, len(log_lines)):
        #             if z_pattern.search(log_lines[j]):
        #                 modsec_Entry.append(log_lines[j].rstrip())
        #                 modsec_Table.append(modsec_Entry)
        #                 i = j + 1
        #                 break
        #             else:
        #                 modsec_Entry.append(log_lines[j].rstrip())
        #     i += 1
        # current_size = log_file.tell()
        # log_file.close()
        # return modsec_Table, current_size
        # # end debug code

    except FileNotFoundError:
        logger.error("File not found")
        return "error", 0
    except Exception as e:
        logger.error(f"Error while read file {e}")
        return "error", 0


def process_violation(violation, session):
    violation_detail = []
    if violation['audit_data']:
        for rule_violation in violation['audit_data']['messages']:
            list_tag = []
            if "libinjection" in rule_violation:
                if "SQLi" in rule_violation:
                    list_tag = ["attack-sqli"]
                elif "XSS" in rule_violation:
                    list_tag = ["attack-xss"]
                else:
                    logger.info("libinjection tag unknown")
                    print("libinjection tag unknown")
            else:
                list_tag = tag.findall(rule_violation)
            block_msg = msg.search(rule_violation).group()
            try:
                matched_info = matched.search(rule_violation).group()
            except Exception as e:
                logger.error(f"Matched Data {e}")
                matched_info = ""
            rule_info = rule_id.search(rule_violation).group()
            detail = {
                "original": rule_violation,
                "list_tag": list_tag,
                "msg": block_msg,
                "matched_info": matched_info,
                "rule_id": rule_info,
                # "group_rule": group_rule_name,
                "system_action": "Block"
            }
            if "ModSecurity: Access denied" in rule_violation:
                violation_detail.append(detail)
            elif "ModSecurity: Warning" in rule_violation:
                if SAVE_WARNING == 1:
                    detail["system_action"] = "Warning"
                    violation_detail.append(detail)
                else:
                    logger.debug("Action Warning, don't save")
            else:
                logger.debug("Action not in Warning and Denied")
    #print("aaaaaa: ", violation_detail)
    return violation_detail


def process_group_website_name(website_domain, session):
    website_obj = session.query(WebsiteBase.group_website_id). \
        filter(WebsiteBase.website_domain.__eq__(website_domain)).first()
    if website_obj is not None:
        group_website_name_obj = session.query(GroupWebsiteBase.name). \
            filter(GroupWebsiteBase.id.__eq__(website_obj.group_website_id)).first()
        if group_website_name_obj:
            return group_website_name_obj.name
    return "UNKNOWN GROUP WEBSITE"


def save_to_database(violation, rules, session):
    violation_header = violation["request"]["headers"]
    website_domain = get_website_domain(violation_header)
    blocked_time = violation["transaction"]["time"]
    attacker_ip = violation["transaction"]["remote_address"]
    attacker_port = violation["transaction"]["remote_port"]
    local_ip=violation["transaction"]["local_address"]
    local_port = violation["transaction"]["local_port"]
    resp_status = violation["response"]["status"]
    request_header = json_to_string(violation["request"])
    attacker_country = find_country(attacker_ip)
    group_website = process_group_website_name(website_domain, session)
    cdb = ClickhouseBase()
    for rule in rules: 
        violation_code = rule["original"].encode("utf-8")

        monitor_waf_obj = MonitorWAF(website_domain=website_domain,
                                     group_website=group_website,
                                     attacker_ip=attacker_ip,
                                     attacker_country=attacker_country,
                                     system_action=rule["system_action"],
                                     request_header=request_header,
                                     matched_info=rule["matched_info"],
                                     violation_code=str(base64.b64encode(violation_code), "utf-8"),
                                     rule_id = rule['rule_id'],
                                     attacker_port = attacker_port,
                                     local_ip = local_ip,
                                     local_port = local_port,
                                     resp_status = resp_status
                                     )
        try:
            cdb.insert([monitor_waf_obj])
        except Exception as e:
            logger.error(f"{e}")
    print("DONE")


def get_website_domain(violation_header):
    if "Host" in violation_header:
        website_domain = violation_header["Host"]
    else:
        website_domain = violation_header["host"]
    return website_domain


def main():
    # init, read file and calculate file size
    print("Monitor WAF")
    log_file = open(LOG_FILE_DIR, 'r')
    log_file.seek(0, 2)
    last_size = log_file.tell()
    log_file.close()
    while True:
        session, engine_connect = ORMSession_alter()
        print(last_size)
        logger.debug(last_size)
        list_content, last_size = process_audit_log(last_size)
        if isinstance(list_content, str) and list_content in 'error':
            logger.debug('No audit log found')
            print('No audit log found')
        elif isinstance(list_content, list) and len(list_content) == 0:
            logger.debug('No events found in the log file')
            print('No events found in the log file')
        else:
            for content in list_content:
                violation = process_log_to_info(content)
                rules = process_violation(violation, session)

                violation_header = violation["request"]["headers"]
                if "host" in violation_header or "Host" in violation_header:
                    website_domain = get_website_domain(violation_header)
                    website_obj = session.query(WebsiteBase). \
                        filter(WebsiteBase.website_domain.__eq__(website_domain)).first()
                        # save database
                    if len(rules) > 0 and website_obj is not None:
                        save_to_database(violation, rules, session)
                        print(f"Violation processed")
                    elif len(rules) > 0:
                        logger.debug(f"Violation {website_domain} not in database")
                        print(f"Violation {website_domain} not in database")
                    else:
                        logger.debug(f"Transaction don't have Violation")
                        print(f"Transaction don't have Violation")
                else:
                    logger.debug(f"Transaction don't have Host")
                    print(f"Transaction don't have Host")
        session.close()
        engine_connect.dispose()
        time.sleep(5)


if __name__ == '__main__':
    logger = c_logger(MONITOR_LOG_DIR + '/monitor-waf-service.log').log_writer
    while not check_database_available():
        logger.error("Database not available yet")
        time.sleep(1)
    main()
