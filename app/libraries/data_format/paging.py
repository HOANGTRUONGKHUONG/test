def reformat_data_with_paging(list_data, number_of_item, limit, offset):
    data = {
        "paging": {
            "total": int(number_of_item),
            "limit": int(limit),
            "offset": int(offset)
        },
        "data": list_data
    }

    return data


def verify_paging_parameters(http_parameters):
    if "limit" not in http_parameters:
        http_parameters["limit"] = 10
    if "offset" not in http_parameters:
        http_parameters["offset"] = 0
    verify = ""
    if "limit" in http_parameters and not str(http_parameters["limit"]).isdigit():
        verify += "limit is not digit, "
        # set to default value
        http_parameters["limit"] = 10
    if "offset" in http_parameters and not str(http_parameters["offset"]).isdigit():
        verify += "offset is not digit, "
        # set to default value
        http_parameters["offset"] = 0
    if ("orderBy" or "orderType") not in http_parameters:
        http_parameters["orderBy"] = "id"
        http_parameters["orderType"] = "asc"
    return verify


def get_average_data(data, rec_num, param):
    rec_num = int(rec_num)
    try:
        _data = []
        if len(data) < rec_num:
            return data
        avg_num = len(data) // rec_num
        arr = []
        for i in range(avg_num, len(data), avg_num):
            arr.append(i)
        arr.append(0)
        arr.append(len(data))
        arr = list(sorted(set(arr)))
        for i in range(len(arr) - 1):
            d = {}
            for p in param:
                d[p] = 0
            for t in range(arr[i], arr[i + 1]):
                for p in param:
                    d[p] += data[t][p]
            for p in param:
                d[p] /= avg_num
            for p in data[0]:
                if p not in param:
                    d[p] = data[arr[i]][p]
            _data.append(d)
        return _data
    except Exception as exp:
        print(exp)
        return []
