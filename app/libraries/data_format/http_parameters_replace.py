def replace_param(http_parameters_dict, wrong_param, correct_param):
    if wrong_param in http_parameters_dict:
        http_parameters_dict[correct_param] = http_parameters_dict[wrong_param]
        del http_parameters_dict[wrong_param]
    return http_parameters_dict
