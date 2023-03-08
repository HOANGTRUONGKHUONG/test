def list_to_string(list_data, dc):
    return dc.join(list_data)


def string_to_list(string_data, dc):
    try:
        data = string_data.split(dc)
    except Exception as e:
        print(e)
        data = None
    return data


def string_to_json(string_data):
    import json
    try:
        json_data = json.loads(string_data)
    except Exception as e:
        print(e)
        return {}
    return json_data


def json_to_string(json_data):
    import json
    try:
        string_data = json.dumps(json_data)
    except Exception as e:
        print(e)
        return "{}"
    return string_data


def dict_to_list(dict):
    list_data = []
    for key, value in dict.items():
        temp = [key, value]
        list_data.append(temp)
    return list_data
