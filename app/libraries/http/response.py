from flask import jsonify


def status_code_200(message, data):
    result = {
        'status': 200,
        'message': str(message),
        'data': data
    }
    response = jsonify(result)
    response.headers["Server"] = "BWAF"
    return response

def status_code_201(message):
    result = {
        'status': 200,
        'message': str(message)
    }
    response = jsonify(result)
    response.status_code = 200
    response.headers["Server"] = "BWAF"
    return response


def get_status_code_200(data):
    response = jsonify(data)
    response.status_code = 200
    response.headers["Server"] = "BWAF"
    return response


def status_code_400(message):
    result = {
        'status': 400,
        'message': str(message)
    }
    response = jsonify(result)
    response.status_code = 200
    response.headers["Server"] = "BWAF"
    return response


def status_code_401(message):
    result = {
        'status': 401,
        'message': str(message)
    }
    response = jsonify(result)
    response.status_code = 200
    response.headers["Server"] = "BWAF"
    return response


def status_code_500(message):
    result = {
        'status': 500,
        'message': str(message)
    }
    response = jsonify(result)
    response.status_code = 200
    response.headers["Server"] = "BWAF"
    return response
