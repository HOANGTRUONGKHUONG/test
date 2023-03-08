import os
import time
import shutil

import nginx
from app.libraries.ORMBase import ORMSession_alter
from app.libraries.inout.file import write_text_file
from app.libraries.system.shell import run_command
from app.libraries.http.response import status_code_400
from app.model import WebsiteBase, DdosApplicationWebsiteBase, DDosApplicationBase, DDosApplicationUriBase, URIBase, \
    WebLimitBandwidthBase, LimitBandwidthHaveUrlBase, ActiveHealthCheckBase, WebsiteListenBase
from app.setting import NGINX_CONFIG_DIR


def ngx_config_backup():
    # copy 2 folder conf.d va group_website tu thu muc /etc/nginx ra folder /tmp/nginx_backup_config
    nginx_backup_dir = "/tmp/nginx_backup_config"
    if os.path.exists(nginx_backup_dir):
        shutil.rmtree(nginx_backup_dir)
    shutil.copytree(f"{NGINX_CONFIG_DIR}/conf.d", "/tmp/nginx_backup_config/conf.d")
    shutil.copytree(f"{NGINX_CONFIG_DIR}/group_website", "/tmp/nginx_backup_config/group_website")
    shutil.copytree(f"{NGINX_CONFIG_DIR}/ssl", "/tmp/nginx_backup_config/ssl")


def ngx_config_remove_backup():
    nginx_backup_dir = "/tmp/nginx_backup_config"
    if os.path.exists(nginx_backup_dir):
        shutil.rmtree(nginx_backup_dir)


def ngx_config_rollback():
    shutil.rmtree(f"{NGINX_CONFIG_DIR}/conf.d")
    shutil.rmtree(f"{NGINX_CONFIG_DIR}/group_website")
    shutil.rmtree(f"{NGINX_CONFIG_DIR}/ssl")
    # copy 2 folder conf.d va group_website backup tu /tmp/nginx_backup_config ve thu muc /etc/nginx
    shutil.copytree("/tmp/nginx_backup_config/conf.d", f"{NGINX_CONFIG_DIR}/conf.d")
    shutil.copytree("/tmp/nginx_backup_config/group_website", f"{NGINX_CONFIG_DIR}/group_website")
    shutil.copytree("/tmp/nginx_backup_config/ssl", f"{NGINX_CONFIG_DIR}/ssl")


def ngx_remove_config(domain):
    try:
        shutil.rmtree(f"{NGINX_CONFIG_DIR}/conf.d/{domain}")
        os.remove(f"{NGINX_CONFIG_DIR}/conf.d/{domain}.conf")
        if ngx_check_config():
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def ngx_remove_group_website_config(group_website_id):
    rules_path = f"{NGINX_CONFIG_DIR}/group_website/group_website_{group_website_id}_rules.conf"
    status_path = f"{NGINX_CONFIG_DIR}/group_website/group_website_{group_website_id}_status.conf"
    try:
        if os.path.exists(rules_path):
            os.remove(rules_path)
        if os.path.exists(status_path):
            os.remove(status_path)
        if ngx_check_config():
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def ngx_upstream_config(domain, list_upstream):
    # config nginx webserver upstream block
    upstream_name = f"upstream_{domain}"
    upstream_data = nginx.Upstream(upstream_name)
    for upstream in list_upstream:
        upstream_ip_port = f"{upstream['ip']}:{upstream['port']}"
        if upstream["type"] == "main":
            # max_fails: the number of unsuccessful attempts to communicate with the server default is 3
            # in v2 can make it to be adjustable
            upstream_main = f"{upstream_ip_port} max_fails=3"
            upstream_data.add(nginx.Key("server", upstream_main))
        elif upstream["type"] == "backup":
            # backup: marks the server as a backup server
            # It will be passed requests when the primary servers are unavailable
            upstream_backup = f"{upstream_ip_port} backup"
            upstream_data.add(nginx.Key("server", upstream_backup))
        elif upstream["type"] == "load balancing":
            # weight: sets the weight of the server, by default, 1.
            # add more upstream, weight, missing weight in v1, need to add weight param in v2
            # using Weighted load balancing
            upstream_lb = f"{upstream_ip_port} weight=1"
            upstream_data.add(nginx.Key("server", upstream_lb))
        else:
            pass
    return upstream_data


def ngx_server_config(domain, listened, list_upstream):
    server_data = nginx.Server()
    listen_port = f"{str(listened['main'])}{' ssl http2' if listened['protocol'] == 'HTTPS' else ''}"
    listen_port6 = f"[::]:{str(listened['main'])}{' ssl http2' if listened['protocol'] == 'HTTPS' else ''}"
    server_data.add(
        nginx.Key("listen", listen_port),
        nginx.Key("listen", listen_port6),
        nginx.Key("server_name", domain),
        nginx.Key("#include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/waf_{domain}.conf"),
        nginx.Key("include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/ips_{domain}.conf"),
        nginx.Key('include', f'{NGINX_CONFIG_DIR}/conf.d/{domain}/cache_{domain}.conf'),
        nginx.Key('include', f'{NGINX_CONFIG_DIR}/conf.d/{domain}/site_other.conf'),
        nginx.Key('include', f'{NGINX_CONFIG_DIR}/conf.d/{domain}/off_rule.conf'),
        nginx.Key('include', '/home/bwaf/bwaf/app/libraries/configuration/detect_only.conf'),
       # nginx.Key('include', f'{NGINX_CONFIG_DIR}/conf.d/{domain}/{domain}_status.conf'),
        # in v2 can make a config what http status to switch to next upstream
        nginx.Key('proxy_next_upstream', 'http_404 http_502 http_504')
    )
    if listened['protocol'] == 'HTTPS':
        server_data.add(
            nginx.Key("ssl_certificate", f"{NGINX_CONFIG_DIR}/ssl/{str(listened['ssl_id'])}.crt"),
            nginx.Key("ssl_certificate_key", f"{NGINX_CONFIG_DIR}/ssl/{str(listened['ssl_id'])}.key"),
            # only use tls v1.2 and v1.3
            nginx.Key("ssl_protocols", "TLSv1.2 TLSv1.3"),
        )

    sslOffloadMode = True
    for upstream in list_upstream:
        if upstream['type'] == "main":
            proxy_pass = f"{'https' if upstream['protocol'] == 'HTTPS' else 'http'}://upstream_{domain}"
            if upstream['protocol'] == "HTTPS":
                sslOffloadMode = False
                ssl_id = upstream['ssl']['id']
    if sslOffloadMode:
        location = nginx.Location("/",
                                nginx.Key("include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/cache_root_{domain}.conf"),
                                nginx.Key("proxy_pass", proxy_pass),
                                nginx.Key("include", f"{NGINX_CONFIG_DIR}/proxy.conf"),
                                nginx.Key("include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/ips_root_{domain}.conf")
                                )
    else:
        location = nginx.Location("/",
                                nginx.Key("include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/cache_root_{domain}.conf"),
                                nginx.Key("proxy_pass", proxy_pass),
                                nginx.Key("include", f"{NGINX_CONFIG_DIR}/proxy.conf"),
                                nginx.Key("include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/ips_root_{domain}.conf"),
                                nginx.Key("proxy_ssl_certificate", f"{NGINX_CONFIG_DIR}/ssl/{str(ssl_id)}.crt"),
                                nginx.Key("proxy_ssl_certificate_key", f"{NGINX_CONFIG_DIR}/ssl/{str(ssl_id)}.key"),
                                nginx.Key("proxy_ssl_protocols", "TLSv1.2 TLSv1.3"),
                                )
    server_data.add(location)
    return server_data


def ngx_website_main_config(domain, list_upstream, listened):
    nginx_conf = nginx.Conf()
    upstream_block = ngx_upstream_config(domain, list_upstream)
    server_block = ngx_server_config(domain, listened, list_upstream)
    nginx_conf.add(upstream_block)
    nginx_conf.add(
        nginx.Key("proxy_cache_path", f"/tmp/{domain} levels=1:2 keys_zone={domain}:10m max_size=3000m inactive=60m")
    )
    nginx_conf.add(server_block)
    nginx_conf.add(
        nginx.Key("include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/redirect_{domain}.conf"),
        nginx.Key("include", f"{NGINX_CONFIG_DIR}/conf.d/{domain}/ips_server_{domain}.conf")
    )
    nginx.dumpf(nginx_conf, f"{NGINX_CONFIG_DIR}/conf.d/{domain}.conf")
    return True


def ngx_cache_config(domain, proxy_pass):
    cache_conf = nginx.Conf()
    cache_conf.add(
        nginx.Location(r"~* \.(?:rss|atom)$",
                       nginx.Key("expires", "1h"),
                       nginx.Key("proxy_cache", domain),
                       nginx.Key("proxy_cache_key", "$scheme$request_method$host$request_uri"),
                       nginx.Key("proxy_cache_methods", "GET HEAD POST"),
                       nginx.Key("proxy_cache_min_uses", "3"),
                       nginx.Key("proxy_cache_valid", "200 30m"),
                       nginx.Key("proxy_cache_use_stale",
                                 "error timeout invalid_header updating http_500 http_502 http_504 http_404"),
                       nginx.Key("proxy_cache_lock", "on"),
                       nginx.Key("proxy_pass", proxy_pass),
                       nginx.Key("include", f"{NGINX_CONFIG_DIR}/proxy.conf")
                       ),
        nginx.Location(r"~* \.(?:jpg|jpeg|gif|png|ico|cur|gz|svg|svgz|mp4|ogg|ogv|webm|htc)$",
                       nginx.Key("expires", "1M"),
                       nginx.Key("proxy_cache", domain),
                       nginx.Key("proxy_cache_key", "$scheme$request_method$host$request_uri"),
                       nginx.Key("proxy_cache_methods", "GET HEAD POST"),
                       nginx.Key("proxy_cache_min_uses", "3"),
                       nginx.Key("proxy_cache_valid", "200 30m"),
                       nginx.Key("proxy_cache_use_stale",
                                 "error timeout invalid_header updating http_500 http_502 http_504 http_404"),
                       nginx.Key("proxy_cache_lock", "on"),
                       nginx.Key("access_log", "off"),
                       nginx.Key("proxy_pass", proxy_pass),
                       nginx.Key("include", f"{NGINX_CONFIG_DIR}/proxy.conf")
                       ),
        nginx.Location(r"~* \.(?:css|js)$",
                       nginx.Key("expires", "1y"),
                       nginx.Key("proxy_cache", domain),
                       nginx.Key("proxy_cache_key", "$scheme$request_method$host$request_uri"),
                       nginx.Key("proxy_cache_methods", "GET HEAD POST"),
                       nginx.Key("proxy_cache_min_uses", "3"),
                       nginx.Key("proxy_cache_valid", "200 30m"),
                       nginx.Key("proxy_cache_use_stale",
                                 "error timeout invalid_header updating http_500 http_502 http_504 http_404"),
                       nginx.Key("proxy_cache_lock", "on"),
                       nginx.Key("access_log", "off"),
                       nginx.Key("proxy_pass", proxy_pass),
                       nginx.Key("include", f"{NGINX_CONFIG_DIR}/proxy.conf")
                       )
    )
    nginx.dumpf(cache_conf, f"{NGINX_CONFIG_DIR}/conf.d/{domain}/cache_{domain}.conf")
    cache_root_conf = nginx.Conf()
    cache_root_conf.add(
        nginx.Key("proxy_cache", domain),
        nginx.Key("proxy_cache_key", "$scheme$request_method$host$request_uri$cookie_user"),
        nginx.Key("proxy_cache_methods", "GET HEAD"),
        nginx.Key("proxy_cache_min_uses", "3"),
        nginx.Key("proxy_cache_valid", "202 302 10m"),
        nginx.Key("proxy_cache_valid", "301 1h"),
        nginx.Key("proxy_cache_valid", "any 1m"),
        nginx.Key("proxy_cache_use_stale", "error timeout invalid_header updating http_500 http_502 http_504 http_404"),
        nginx.Key("proxy_cache_lock", "on")
    )
    nginx.dumpf(cache_root_conf, f"{NGINX_CONFIG_DIR}/conf.d/{domain}/cache_root_{domain}.conf")
    return True


def ngx_redirect_config(domain, listened):
    conf = nginx.Conf()
    print ("AAAAAAAAA", listened["redirect"])
    for port in listened["redirect"]:
        if port == "":
            continue
        redirect_conf = nginx.Server()
        redirect_conf.add(
            nginx.Key("listen", str(port)),
            nginx.Key("listen", f"[::]:{str(port)}"),
            nginx.Key("server_name", domain),
            nginx.Key("return", f"301 {'https' if listened['protocol'] == 'HTTPS' else 'http'}://"
                                f"$server_name:{listened['main']}$request_uri")
        )
        conf.add(redirect_conf)
    nginx.dumpf(conf, f"{NGINX_CONFIG_DIR}/conf.d/{domain}/redirect_{domain}.conf")
    return True


def ngx_website_config(domain, list_upstream, listened, cache):
    proxy_pass = f"{'https' if listened['protocol'] == 'HTTPS' else 'http'}://upstream_{domain}"

    conf_path = f"{NGINX_CONFIG_DIR}/conf.d/{domain}"
    if not os.path.exists(conf_path):
        os.mkdir(conf_path)
    ngx_website_main_config(domain, list_upstream, listened)
    if cache:
        ngx_cache_config(domain, proxy_pass)
    else:
        write_text_file(f"{conf_path}/cache_{domain}.conf", "")
        write_text_file(f"{conf_path}/cache_root_{domain}.conf", "")
    if len(listened["redirect"]) > 0:
        ngx_redirect_config(domain, listened)
    else:
        write_text_file(f"{conf_path}/redirect_{domain}.conf", "")
    write_text_file(f"{conf_path}/ips_{domain}.conf", "")
    write_text_file(f"{conf_path}/ips_server_{domain}.conf", "")
    write_text_file(f"{conf_path}/ips_root_{domain}.conf", "")
    write_text_file(f"{conf_path}/waf_{domain}.conf", "")
    write_text_file(f"{conf_path}/site_other.conf", "")
    write_text_file(f"{conf_path}/off_rule.conf", "")
    if ngx_check_config():
        return True
    else:
        return False

def active_health_check():
    config = """"""
    session,engine_connect = ORMSession_alter()
    try:
        website_health_check = session.query(WebsiteBase).all()
        for domain in website_health_check:
            if domain.health_check_status == 0:
                continue
            health_check = session.query(ActiveHealthCheckBase).filter(ActiveHealthCheckBase.website_id.__eq__(domain.id)).first()
            listened = session.query(WebsiteListenBase).filter(WebsiteListenBase.website_id.__eq__(domain.id)).first()
                
            config += """
            local ok, err = hc.spawn_checker{{
                    shm = "healthcheck",  
                    upstream = "upstream_{web}", 
                    type = "{http_or_https}", 
                    http_req = "GET {url} {HTTP_OR_HTTPS}/1.0\\r\\nHost: {web}\\r\\n\\r\\n",
                    port = {port}, 
                    interval = {interval}, 
                    timeout = {timeout},  
                    fall = {fall},  
                    rise = {rise},  
                    valid_statuses = {valid_statuses},  
                    concurrency = {concurrency},  
                }}
                if not ok then
                    ngx.log(ngx.ERR, "failed to spawn health checker: ", err)
                    return
                end
            """.format(
                web=domain.website_domain,
                http_or_https = "https" if listened.protocol == 'HTTPS' else 'http',
                HTTP_OR_HTTPS = "HTTPS" if listened.protocol == 'HTTPS' else 'HTTP',
                url=health_check.url,
                interval=health_check.interval,
                timeout=health_check.timeout,
                fall=health_check.fall, rise=health_check.rise,
                valid_statuses="{"+health_check.valid_statuses+"}",
                concurrency=health_check.concurrency,
                port="nil" if health_check.port_check =="" else health_check.port_check
            )
        config_health = """
lua_shared_dict healthcheck {size}m;
init_worker_by_lua_block {{
    local hc = require "resty.upstream.healthcheck"
    {config}
}}
        """.format(
            size=health_check.size,
            config=config
        )
        write_text_file(f"{NGINX_CONFIG_DIR}/active_health_check.lua", config_health)
        return True
    except Exception as e:
       # raise e
        session.close()
        engine_connect.dispose()
        return status_code_400("Health.check.failed")


def ngx_check_config():
    check_message = run_command("openresty -t")
    print(check_message)
    if "failed" in str(check_message):
        return False
    return True


def ngx_restart():
    restart_message = run_command("service openresty restart")
    return True


def ngx_reload():
    reload_message = run_command("service openresty reload")
    return True

def monitor_restart():
    time.sleep(2)
    restart_message = run_command("service monitor-api restart")
    return True


def modsecurity_group_website_status_config(status=False):
    config = '''modsecurity off;\n''' if status is False else '''modsecurity on;\n'''
    return config


def ngx_group_website_init_config(group_website_id):
    group_website_path = f"{NGINX_CONFIG_DIR}/group_website"
    try:
        if not os.path.exists(group_website_path):
            os.mkdir(group_website_path)
        write_text_file(file_dir=f"{group_website_path}/group_website_{group_website_id}_rules.conf", content="")
        write_text_file(file_dir=f"{group_website_path}/group_website_{group_website_id}_status.conf",
                        content=modsecurity_group_website_status_config())
        return True
    except Exception as e:
        print(e)
        return False


def ngx_add_website_to_group_website(website_domain, group_website_id):
    nginx_conf = nginx.Conf()
    nginx_conf.add(
        nginx.Key("include", f"{NGINX_CONFIG_DIR}/group_website/group_website_{group_website_id}_status.conf"),
        nginx.Key("modsecurity_rules_file", f"{NGINX_CONFIG_DIR}/group_website/group_website_{group_website_id}_rules.conf")
    )
    nginx.dumpf(nginx_conf, f"{NGINX_CONFIG_DIR}/conf.d/{website_domain}/waf_{website_domain}.conf")
    if ngx_check_config():
        return True
    else:
        return False


def ngx_remove_website_from_group_website(website_domain, check_config=True):
    write_text_file(file_dir=f"{NGINX_CONFIG_DIR}/conf.d/{website_domain}/waf_{website_domain}.conf", content="")
    if check_config:
        if ngx_check_config():
            return True
        else:
            return False
    else:
        return True


def modsecurity_group_website_change_waf_status(group_website_id, waf_status):
    group_website_path = f"{NGINX_CONFIG_DIR}/group_website"
    try:
        write_text_file(file_dir=f"{group_website_path}/group_website_{group_website_id}_status.conf",
                        content=modsecurity_group_website_status_config(status=waf_status))
        return True
    except Exception as e:
        print(e)
        return False


def modsecurity_group_website_rules_change(group_website_id, change_config):
    rule_config = {
        "drupal-exclusion": 1,
        "wordpress-exclusion": 1,
        "nextcloud-exclusion": 1,
        "dokuwiki-exclusion": 1,
        "cpanel-exclusion": 1,
        "xenforo-exclusion": 1,
        "attack-reputation-ip": 1,
        "method-enforcement": 1,
        "attack-dos": 1,
        "attack-reputation-scanner": 1,
        "attack-protocol": 1,
        "attack-lfi": 1,
        "attack-rfi": 1,
        "attack-rce": 1,
        "attack-injection-php": 1,
        "attack-xss": 1,
        "attack-sqli": 1,
        "attack-fixation": 1,
        "language-java": 1,
        "attack-disclosure": 1
    }
    rule_config.update(change_config)
    rule_content = ""
    for rule_tag in rule_config:
        if rule_config[rule_tag] != 1:
            rule_content += f"SecRuleRemoveByTag \"{rule_tag}\"\n"
    group_website_path = f"{NGINX_CONFIG_DIR}/group_website"
    try:
        write_text_file(file_dir=f'{group_website_path}/group_website_{group_website_id}_rules.conf',
                        content=rule_content)
        return True
    except Exception as e:
        print(e)
        return False


# config rule IPS

def ngx_website_ips_server_config(website_detail):
    nginx_conf = nginx.Conf()
    for key, value in website_detail['uri_detail'].items():
        uri_name = key.split('/')[1]
        # XL DDoS Application
        if 'ddos' in value:
            for rule in value['ddos']:
                rule_type = ''.join(rule['rule_type'].split(" "))
                if rule_type == 'type2':
                    nginx_conf.add(
                        nginx.Key("limit_req_zone",
                                  f"$binary_remote_addr zone={rule_type}_{uri_name}_{website_detail['web_id']}:10m"
                                  f" rate={rule['value']}r/s"))
                if rule_type == 'type1':
                    nginx_conf.add(
                        nginx.Key("limit_req_zone",
                                  f"'$binary_remote_addr$request_uri' "
                                  f"zone={rule_type}_{uri_name}_{website_detail['web_id']}:10m"
                                  f" rate={rule['value']}r/s"))
        # XL Bandwith
        if 'bandwith' in value:
            if value['bandwith']['status'] == 1:
                nginx_conf.add(
                    nginx.Key("limit_conn_zone", f"$binary_remote_addr zone=addr_{uri_name}:10m")
                )
    nginx.dumpf(nginx_conf,
                f"{NGINX_CONFIG_DIR}/conf.d/{website_detail['website_name']}/"
                f"ips_server_{website_detail['website_name']}.conf")
    return True


def ngx_website_ips_root_config(website_detail):
    nginx_conf = nginx.Conf()
    for key, value in website_detail['uri_detail'].items():
        if key == "/":
            # XL DDoS Application
            uri_name = key.split('/')[1]
            if "ddos" in value:
                for rule in value['ddos']:
                    rule_type = ''.join(rule['rule_type'].split(" "))
                    nginx_conf.add(
                        nginx.Key("limit_req", f"zone={rule_type}_{uri_name}_{website_detail['web_id']} "
                                               f"burst={rule['value'] - 1} nodelay")
                    )
            # XL Bandwith
            if 'bandwith' in value:
                if value['bandwith']['status'] == 1:
                    nginx_conf.add(
                        nginx.Key("limit_conn", f"addr_{uri_name} {value['bandwith']['site_conn']}"),
                        nginx.Key("limit_rate_after", f"{value['bandwith']['limit_rate_after']}m"),
                        nginx.Key("limit_rate", f"{value['bandwith']['limit_rate']}k")
                    )
        else:
            continue
    nginx.dumpf(nginx_conf,
                f"{NGINX_CONFIG_DIR}/conf.d/{website_detail['website_name']}/"
                f"ips_root_{website_detail['website_name']}.conf")
    return True


def ngx_website_ips_config(website_detail):
    nginx_conf = nginx.Conf()
    for key, value in website_detail['uri_detail'].items():
        # key = 'uri_name'
        if key == "/":
            continue
        uri_name = key.split('/')[1]

        # XL limit_conn addr_{uri} 20;
        if "bandwith" in value:
            if value['bandwith']['status'] == 1:
                nginx_conf.add(nginx.Key("limit_conn", f"addr_{uri_name} {value['bandwith']['sum_conn']}"))

        nginx_location = nginx.Location(f"{key}")
        proxy_pass = f"{'https' if website_detail['website_ssl'] is not None else 'http'}" \
                     f"://upstream_{website_detail['website_name']}{key}"

        # XL DDoS Application
        if "ddos" in value:
            for rule in value['ddos']:
                rule_type = ''.join(rule['rule_type'].split(" "))
                nginx_location.add(nginx.Key("limit_req", f"zone={rule_type}_{uri_name}_{website_detail['web_id']} "
                                                          f"burst={rule['value'] - 1} nodelay"))
            # xong vong lap se luu lai thong tin file.
        # XL Bandwith
        if "bandwith" in value:
            if value['bandwith']['status'] == 1:
                nginx_location.add(
                    nginx.Key("limit_conn", f"addr_{uri_name} {value['bandwith']['site_conn']}"),
                    nginx.Key("limit_rate_after", f"{value['bandwith']['limit_rate_after']}m"),
                    nginx.Key("limit_rate", f"{value['bandwith']['limit_rate']}k")
                )

        nginx_location.add(nginx.Key("proxy_pass", proxy_pass))
        nginx_location.add(nginx.Key("include", "/etc/openresty/proxy.conf"))
        nginx_conf.add(nginx_location)
    nginx.dumpf(nginx_conf,
                f"{NGINX_CONFIG_DIR}/conf.d/{website_detail['website_name']}/ips_{website_detail['website_name']}.conf")
    return True


def dump_ips_empty_config(website_name):
    nginx_conf = nginx.Conf()
    nginx.dumpf(nginx_conf,
                f"{NGINX_CONFIG_DIR}/conf.d/{website_name}/"
                f"ips_server_{website_name}.conf")
    nginx.dumpf(nginx_conf,
                f"{NGINX_CONFIG_DIR}/conf.d/{website_name}/"
                f"ips_root_{website_name}.conf")
    nginx.dumpf(nginx_conf,
                f"{NGINX_CONFIG_DIR}/conf.d/{website_name}/ips_{website_name}.conf")
    return True


def dump_ips_config(website):
    if not website['uri_detail']:
        dump_ips_empty_config(website['website_name'])
    else:
        ngx_website_ips_config(website)
        ngx_website_ips_root_config(website)
        ngx_website_ips_server_config(website)
    return True


def generate_ips_config_data(session, domain):
    websites = {}
    url = []
    list_url = []
    websites_url = []
    bandwitdth_uri = []
    website_inform = session.query(WebsiteBase).filter(WebsiteBase.website_domain.__eq__(domain)).first()
    if website_inform:
        ddos_application = session.query(DdosApplicationWebsiteBase, DDosApplicationBase).outerjoin(
            DDosApplicationBase). \
            filter(DdosApplicationWebsiteBase.website_id.__eq__(website_inform.id)).all()
        # DDoS Application
        if ddos_application:
            for i in ddos_application:
                if i.DDosApplicationBase.active == 1:
                    uri_inform = session.query(DDosApplicationUriBase, URIBase, DDosApplicationBase).outerjoin(
                        URIBase).outerjoin(DDosApplicationBase). \
                        filter(DDosApplicationUriBase.ddos_app_id.__eq__(i.DDosApplicationBase.id)).all()
                    if uri_inform:
                        for uri in uri_inform:
                            if uri.DDosApplicationBase.active == 1:
                                uri_detail = {
                                    "uri": uri.URIBase.uri if uri.URIBase is not None else None,
                                    "rule": uri.DDosApplicationBase.rule_type
                                    if uri.DDosApplicationBase is not None else None,
                                    "value": int(uri.DDosApplicationBase.count / uri.DDosApplicationBase.time) if
                                    uri.DDosApplicationBase is not None else None
                                }
                                list_url.append("/")
                                root = {
                                    "uri": "/",
                                    "rule": i.DDosApplicationBase.rule_type
                                    if i.DDosApplicationBase is not None else None,
                                    "value": int(uri.DDosApplicationBase.count / uri.DDosApplicationBase.time) if
                                    uri.DDosApplicationBase is not None else None
                                }
                                url.append(root)
                                list_url.append(uri.URIBase.uri if uri.URIBase is not None else None)
                                url.append(uri_detail)
                            else:
                                continue
                    else:
                        list_url.append("/")
                        root = {
                            "uri": "/",
                            "rule": i.DDosApplicationBase.rule_type
                            if i.DDosApplicationBase is not None else None,
                            "value": int(i.DDosApplicationBase.count / i.DDosApplicationBase.time) if
                            i.DDosApplicationBase is not None else None
                        }
                        url.append(root)
                else:
                    continue
            websites_url.extend(list(set(list_url)))
        # Bandwidth
        limit_bandwidth = session.query(WebLimitBandwidthBase). \
            filter(WebLimitBandwidthBase.website_id.__eq__(website_inform.id)).all()
        if limit_bandwidth:
            for bandwidth in limit_bandwidth:
                limit_url = session.query(LimitBandwidthHaveUrlBase, URIBase).outerjoin(URIBase). \
                    filter(LimitBandwidthHaveUrlBase.bandwidth_id.__eq__(bandwidth.id)).all()
                limit_bandwidth_data = {"id": bandwidth.id,
                                        "name": bandwidth.name,
                                        "status": bandwidth.status,
                                        "limit_rate": bandwidth.limit_rate,
                                        "limit_rate_after": bandwidth.limit_rate_after,
                                        "sum_conn": bandwidth.sum_conn,
                                        "site_conn": bandwidth.site_conn
                                        }
                for l_uri in limit_url:
                    if l_uri.URIBase.uri is not None:
                        websites_url.append(l_uri.URIBase.uri)
                        bandwidth_data = {
                            'uri_name': l_uri.URIBase.uri,
                            'rule_detail': limit_bandwidth_data
                        }
                        bandwitdth_uri.append(bandwidth_data)
                    else:
                        continue
        website_detail = {
            "web_id": website_inform.id,
            "website_ssl": website_inform.ssl_id,
            "website_name": website_inform.website_domain,
            "uri_detail": export_uri_data(url, list(set(websites_url)), bandwitdth_uri)
        }
        websites.update(website_detail)
        return websites


def export_uri_data(ddos_url, list_url, bandwith_url):
    detail = {}
    for url in list_url:
        type1_value = []
        type2_value = []
        rule_inform = []
        for ddos in ddos_url:
            if url == ddos["uri"]:
                if ddos["rule"] == "type 1":
                    type1_value.append(ddos["value"])
                if ddos["rule"] == "type 2":
                    type2_value.append(ddos["value"])
        if len(type1_value) != 0:
            rule1_inform = {
                "rule_type": "type 1",
                "value": min(type1_value)
            }
            rule_inform.append(rule1_inform)
        if len(type2_value) != 0:
            rule2_inform = {
                "rule_type": "type 2",
                "value": min(type2_value)
            }
            rule_inform.append(rule2_inform)
        if rule_inform:
            detail.update({
                f"{url}": {
                    "ddos": rule_inform
                }
            })
        for bandwith in bandwith_url:
            if bandwith['uri_name'] == url:
                try:
                    detail[f'{url}'].update({
                        "bandwith": bandwith['rule_detail']
                    })
                except:
                    detail.update({
                        f"{url}": {
                            "bandwith": bandwith['rule_detail']
                        }
                    })
    return detail
