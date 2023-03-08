import os

from app.libraries.inout.file import write_text_file
from app.setting import NGINX_CONFIG_DIR

SSL_CONFIG_DIR = NGINX_CONFIG_DIR + "/ssl"


def ssl_config(ssl_id, ssl_key, ssl_cert):
    # verify ssl pair
    write_text_file(SSL_CONFIG_DIR + "/{ssl_id}.key".format(ssl_id=ssl_id), ssl_key)
    write_text_file(SSL_CONFIG_DIR + "/{ssl_id}.crt".format(ssl_id=ssl_id), ssl_cert)
    return True


def remove_ssl(ssl_id):
    try:
        os.remove(SSL_CONFIG_DIR + "/{ssl_id}.key".format(ssl_id=ssl_id))
        os.remove(SSL_CONFIG_DIR + "/{ssl_id}.crt".format(ssl_id=ssl_id))
        return True
    except Exception as e:
        print(e)
        return False
