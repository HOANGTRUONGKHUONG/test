import nginx

from app.setting import NGINX_CONFIG_DIR


def ngx_log_format():
    data_format = nginx.loadf(f'{NGINX_CONFIG_DIR}/conf/nginx.conf')
    data = data_format.filter('Http')
    data_main = ""
    for key in data:
        data_detail = key.filter('Key', 'log_format').__getitem__(0).as_strings
        # Loai bo mot so ky tu thua ben trong doan str.
        form_main = data_detail.replace('log_format main  ', '').replace(';', '') \
            .replace('  ', '').replace('\n', '').replace("'", "")
        data_main = form_main
    return data_main

print(type(ngx_log_format()))
