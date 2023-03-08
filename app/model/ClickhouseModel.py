from infi.clickhouse_orm import Model, DateTimeField, MergeTree, F, Float64Field, Int64Field, StringField


class MonitorConnection(Model):
    datetime = DateTimeField(default=F.now())
    active = Int64Field()
    reading = Int64Field()
    writing = Int64Field()
    waiting = Int64Field()

    engine = MergeTree('datetime', ('active', 'reading', 'writing', 'waiting'))

    @classmethod
    def table_name(cls):
        return 'monitor_connection'


class MonitorDdosApplication(Model):
    datetime = DateTimeField(default=F.now())
    ip_address = StringField()
    attacker_country = StringField()
    rule = StringField()
    website_domain = StringField()
    unlock = Int64Field()
    detail = StringField()

    engine = MergeTree('datetime', ('ip_address', 'attacker_country', 'rule', 'website_domain', 'detail'))

    @classmethod
    def table_name(cls):
        return 'monitor_ddos_application_layer'


class MonitorDdosNetwork(Model):
    datetime = DateTimeField(default=F.now())
    ip_address = StringField()
    attacker_country = StringField()
    rule = StringField()
    website_domain = StringField()
    unlock = Int64Field()
    detail = StringField()

    engine = MergeTree('datetime', ('ip_address', 'attacker_country', 'rule', 'website_domain', 'detail'))

    @classmethod
    def table_name(cls):
        return 'monitor_ddos_network_layer'


class MonitorHTTP(Model):
    datetime = DateTimeField(default=F.now())
    code_1 = Int64Field()
    code_2 = Int64Field()
    code_3 = Int64Field()
    code_4 = Int64Field()
    code_5 = Int64Field()

    engine = MergeTree('datetime', ('code_1', 'code_2', 'code_3', 'code_4', 'code_5'))

    @classmethod
    def table_name(cls):
        return 'monitor_http_status_code'


class MonitorResource(Model):
    datetime = DateTimeField(default=F.now())
    cpu = Float64Field()
    ram = Float64Field()
    disk = Float64Field()

    engine = MergeTree('datetime', ('cpu', 'ram', 'disk'))

    @classmethod
    def table_name(cls):
        return 'monitor_resource'


class MonitorSetting(Model):
    datetime = DateTimeField(default=F.now())
    user_name = StringField()
    ip_address = StringField()
    action = StringField()
    status = Int64Field()
    description = StringField()

    engine = MergeTree('datetime', ('user_name', 'ip_address', 'action', 'status', 'description'))

    @classmethod
    def table_name(cls):
        return 'monitor_setting'


class MonitorTraffic(Model):
    datetime = DateTimeField(default=F.now())
    interface_id = Int64Field()
    input = Float64Field()
    output = Float64Field()
    interface_name = StringField()

    engine = MergeTree('datetime', ('interface_id', 'input', 'output', 'interface_name'))

    @classmethod
    def table_name(cls):
        return 'monitor_traffic'


class MonitorWAF(Model):
    datetime = DateTimeField(default=F.now())
    website_domain = StringField()
    group_website = StringField()
    attacker_ip = StringField()
    attacker_country = StringField()
    group_rule = StringField()
    system_action = StringField()
    request_header = StringField()
    matched_info = StringField()
    violation_code = StringField()

    attacker_port = StringField()
    local_ip = StringField()
    local_port = StringField()
    rule_id = StringField()
    resp_status = StringField()

    engine = MergeTree('datetime', ('website_domain', 'group_website', 'attacker_ip', 'attacker_country', 'group_rule',
                                    'system_action', 'request_header', 'matched_info', 'violation_code', 'attacker_port',
                                    'local_ip', 'local_port', 'rule_id','resp_status'))

    @classmethod
    def table_name(cls):
        return 'monitor_waf'


class MonitorLogin(Model):
    datetime = DateTimeField(default=F.now())
    ip_address = StringField()
    username = StringField()
    login_status = Int64Field()
    engine = MergeTree('datetime', ('ip_address', 'username', 'login_status'))

    @classmethod
    def table_name(cls):
        return 'monitor_login'


class MonitorSiteConnection(Model):
    datetime = DateTimeField(default=F.now())
    site_connect = StringField()
    request_site = Int64Field()
    engine = MergeTree('datetime', ('site_connect', 'request_site'))

    @classmethod
    def table_name(cls):
        return 'monitor_site_connection'


class MonitorIPConnection(Model):
    datetime = DateTimeField(default=F.now())
    ip_connect = StringField()
    request_ip = Int64Field()
    unlock= Int64Field()
    engine = MergeTree('datetime', ('ip_connect', 'request_ip', 'unlock'))

    @classmethod
    def table_name(cls):
        return 'monitor_ip_connection'

class MonitorFileScanned(Model):
    datetime = DateTimeField()
    filename = StringField()
    source_ip = StringField()
    group_website = StringField()
    website = StringField()
    url = StringField()
    message = StringField()
    engine = MergeTree('datetime', ('filename', 'source_ip', 'group_website', 
                        'website','url','message'))

    @classmethod
    def table_name(cls):
        return 'monitor_file_scanned'