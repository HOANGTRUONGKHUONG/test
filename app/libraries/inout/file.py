import json
import os
from os import listdir
from os.path import isfile, join, getsize, islink
import yaml

def opener(path, flags):
    return os.open(path, flags, 0o777)

def write_text_file(file_dir, content, append=False):
    try:
        with open(file_dir, "a" if append else "w", opener=opener) as file:
            file.write(content)
        return True
    except Exception as e:
        print(e)
        return False


def read_text_file(file_dir):
    with open(file_dir, "r") as file:
        data = file.read()
    return data


def write_json_file(file_dir, object_data):
    try:
        json_data = json.dumps(object_data)
        with open(file_dir, "w") as json_file:
            json_file.write(json_data)
        return True
    except Exception as e:
        print(e)
        return False


def read_json_file(file_dir):
    try:
        with open(file_dir, 'r') as json_file:
            data = json_file.read()
        return json.loads(data)
    except Exception as e:
        raise e


def write_yaml_file_from_object(file_dir, object_data):
    try:
        with open(file_dir, 'w') as yaml_file:
            yaml.dump(object_data, yaml_file)
        return True
    except Exception as e:
        print(e)
        return False


def read_yaml_file_to_object(file_dir):
    try:
        with open(file_dir, 'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
            return yaml_data
    except Exception as e:
        print(e)
        return False


def get_size(path):
    summary = 0
    if isfile(path):
        return getsize(path)
    elif not islink(path):
        arr = listdir(path)
        for i in arr:
            try:
                summary = summary + get_size(path + f"/{i}")
            except Exception as e:
                print(e)
                summary = summary
        return summary


def list_all_file_in_folder(folder):
    only_files = [f for f in listdir(folder) if isfile(join(folder, f))]
    return only_files


def parsed_json(json):
    return_data = {}
    if json['dns']:
        return_data.update({
            'nameservers': {
                'addresses': json['dns']
            }
        })
    if "parameters" in json:
        return_data.update({"parameters": {"mode": json["parameters"], "mii-monitor-interval": 1}})
    if "interfaces" in json:
        return_data.update({"interfaces": json["interfaces"]})
    if not json['ipv4_address'] and not json['ipv6_address']:
        return return_data
    if not json['ipv4_address']:
        append_data = {
            'addresses': json['ipv6_address']
        }
        if json["gateway_ipv6"]:
            append_data.update({'gateway6': json['gateway_ipv6']})
        return_data.update(append_data)
    elif not json['ipv6_address']:
        append_data = {
            'addresses': json['ipv4_address']
        }
        if json['gateway_ipv4']:
            append_data.update({'gateway4': json['gateway_ipv4']})
        return_data.update(append_data)
    else:
        append_data = {
            'addresses': json['ipv4_address'] + json['ipv6_address'],
            'gateway4': json['gateway_ipv4'],
            'gateway6': json['gateway_ipv6']
        }
        return_data.update(append_data)
    return return_data
