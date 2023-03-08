from datetime import datetime
from os import cpu_count
from sqlalchemy import Column, Integer, String, TEXT, ForeignKey, \
    DateTime, Text, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class ReportFormBase(Base):
    __tablename__ = "object_system_report_form"
    id = Column(Integer, primary_key=True, autoincrement=True)
    html_form = Column(String)


class BackupScheduleBase(Base):
    __tablename__ = "backup_schedule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String)
    datetime = Column(DateTime)
    account = Column(String)
    mode = Column(String)
    start = Column(String)
    period = Column(String)
    period_id = Column(Integer, ForeignKey("object_period.id"), nullable=True)
    object_period = relationship("PeriodBase", backref=backref("object_period_backup_schedule"), uselist=True)


class DDosApplicationUriBase(Base):
    __tablename__ = "ddos_application_has_uri"
    ddos_app_id = Column(Integer, ForeignKey("ddos_application_layer.id"), nullable=True, primary_key=True)
    uri_id = Column(Integer, ForeignKey("ddos_application_layer_uri.id"), nullable=True, primary_key=True)
    ddos_application_layer = relationship("DDosApplicationBase", backref=backref("ddos_application_layer_has_uri"),
                                          uselist=True)
    ddos_application_layer_uri = relationship("URIBase", backref=backref("ddos_application_layer_uri"), uselist=True)


class DdosApplicationWebsiteBase(Base):
    __tablename__ = "ddos_application_has_website"
    website_id = Column(Integer, ForeignKey("object_website.id"), nullable=True, primary_key=True)
    ddos_app_id = Column(Integer, ForeignKey("ddos_application_layer.id"), nullable=True, primary_key=True)
    object_website = relationship("WebsiteBase", backref=backref("object_website_ddos", uselist=True))
    ddos_application_layer = relationship("DDosApplicationBase", backref=backref("ddos_application_layer"),
                                          uselist=True)


class ScheduleAccountBase(Base):
    __tablename__ = "scan_schedule_has_account"
    account_id = Column(Integer, ForeignKey("object_account.id"), nullable=True, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("scan_web_schedule.id"), nullable=True, primary_key=True)
    object_account = relationship("AccountBase", backref=backref("object_account_schedule", uselist=True))


class ScheduleWebsiteBase(Base):
    __tablename__ = "scan_schedule_has_website"
    website_id = Column(Integer, ForeignKey("object_website.id"), nullable=True, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("scan_web_schedule.id"), nullable=True, primary_key=True)
    object_website = relationship("WebsiteBase", backref=backref("object_website_schedule", uselist=True))


class ReportAccountBase(Base):
    __tablename__ = "object_report_has_account"
    object_report_id = Column(Integer, ForeignKey("object_system_report.id"), nullable=True, primary_key=True)
    object_account_id = Column(Integer, ForeignKey("object_account.id"), nullable=True, primary_key=True)
    object_system_report = relationship("ReportBase", backref=backref("object_system_report", uselist=True))
    object_account = relationship("AccountBase", backref=backref("object_account_report", uselist=True))


class ReportBase(Base):
    __tablename__ = "object_system_report"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    state = Column(Integer)
    report_form = Column(String)
    period_id = Column(Integer, ForeignKey("object_period.id"), nullable=True)
    mail_sender_id = Column(Integer, ForeignKey("object_mail_sender.id"), nullable=True)
    object_period = relationship("PeriodBase", backref=backref("object_period_report", uselist=True))
    object_mail_sender = relationship("MailSenderBase", backref=backref("object_mail_sender", uselist=True))


class PeriodBase(Base):
    __tablename__ = "object_period"
    id = Column(Integer, primary_key=True)
    period_name = Column(String)


class AccountBase(Base):
    __tablename__ = "object_account"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String)
    phone_number = Column(String)


class DDosApplicationBase(Base):
    __tablename__ = "ddos_application_layer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    count = Column(Integer)
    time = Column(Integer)
    block_time = Column(Integer)
    active = Column(Integer)
    status = Column(String)
    rule_type = Column(String)
    group_website_id = Column(Integer, ForeignKey("object_group_website.id"), nullable=True)
    object_group_website = relationship("GroupWebsiteBase", backref=backref("object_group_website", uselist=True))


class URIBase(Base):
    __tablename__ = "ddos_application_layer_uri"
    id = Column(Integer, primary_key=True, autoincrement=True)
    uri = Column(String)


class DDosNetworkLayerBase(Base):
    __tablename__ = "ddos_network_layer"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    threshold = Column(Integer)
    duration = Column(Integer)
    block_duration = Column(Integer)
    state = Column(Integer)
    alert = Column(Integer)


class DeadTokenBase(Base):
    __tablename__ = "dead_token"
    id = Column(Integer, primary_key=True)
    token = Column(String)
    type = Column(String)


class GroupWebsiteBase(Base):
    __tablename__ = "object_group_website"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    group_website_status = Column(Integer)
    website = relationship("WebsiteBase")


class HighAvailabilityBase(Base):
    __tablename__ = "high_availability"
    id = Column(Integer, primary_key=True)
    high_availability_mode = Column(Integer, ForeignKey("high_availability_mode.id"))
    device_priority = Column(Integer)
    group_name = Column(String)
    group_password = Column(String)
    heartbeat_interface_id = Column(Integer, ForeignKey("network_interface.id"))
    heartbeat_network = Column(String)
    heartbeat_netmask = Column(String)


class HighAvailabilityInterfaceBase(Base):
    __tablename__ = "high_availability_virtual_interface"
    id = Column(Integer, ForeignKey("network_interface.id"), primary_key=True)
    virtual_ip_address = Column(String)
    enable = Column(Integer)
    priority = Column(Integer)


class HighAvailabilityModeBase(Base):
    __tablename__ = "high_availability_mode"
    id = Column(Integer, primary_key=True)
    mode_name = Column(String)


class IpBlacklistBase(Base):
    __tablename__ = "object_ip_blacklist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String)
    netmask = Column(String)
    description = Column(String)


class IpWhitelistBase(Base):
    __tablename__ = "object_ip_whitelist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String)
    netmask = Column(String)
    description = Column(String)


class LicenceBase(Base):
    __tablename__ = "licence"
    licence = Column(String, primary_key=True)
    expiration_date = Column(DateTime)


class MailSenderBase(Base):
    __tablename__ = "object_mail_sender"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    password = Column(String)
    server_id = Column(Integer, ForeignKey("object_mail_server.id"), nullable=True)
    mail_server = relationship("MailServerBase", backref=backref("object_mail_server", uselist=True))


class MailServerBase(Base):
    __tablename__ = "object_mail_server"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    end_point = Column(String)


class MonitorSettingBase(Base):
    __tablename__ = "monitor_setting"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    user_name = Column(String)
    ip_address = Column(String)
    action = Column(String)
    status = Column(Integer)
    description = Column(String)


class MonitorDdosNetworkBase(Base):
    __tablename__ = "monitor_ddos_network_layer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String)
    datetime = Column(String)
    attacker_country = Column(String)
    rule = Column(String)
    unblock = Column(Integer)
    detail = Column(TEXT)


class MonitorDdosApplicationBase(Base):
    __tablename__ = "monitor_ddos_application_layer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String)
    datetime = Column(String)
    attacker_country = Column(String)
    rule = Column(String)
    website_domain = Column(String)
    unlock = Column(String)
    detail = Column(TEXT)


class MonitorBandwidthIPBase(Base):
    __tablename__ = "monitor_ip_bandwidth"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    interface_id = Column(Integer)
    value = Column(Text)


class MonitorConnectionBase(Base):
    __tablename__ = "monitor_connection"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    active = Column(Integer)
    reading = Column(Integer)
    writing = Column(Integer)
    waiting = Column(Integer)


class MonitorHTTPBase(Base):
    __tablename__ = "monitor_http_status_code"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    code_1 = Column(Integer)
    code_2 = Column(Integer)
    code_3 = Column(Integer)
    code_4 = Column(Integer)
    code_5 = Column(Integer)


class MonitorResourceBase(Base):
    __tablename__ = "monitor_resource"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    ram = Column(Float)
    cpu = Column(Float)
    disk = Column(Float)


class MonitorTrafficBase(Base):
    __tablename__ = "monitor_traffic"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    interface_id = Column(Integer)
    input = Column(String)
    output = Column(String)


class MonitorWAFBase(Base):
    __tablename__ = "monitor_waf"
    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime)
    website_domain = Column(String)
    group_website = Column(String)
    attacker_ip = Column(String)
    attacker_country = Column(String)
    group_rule = Column(String)
    system_action = Column(String)
    request_header = Column(Text)
    matched_info = Column(Text)
    violation_code = Column(Text)


class NetworkInterfaceBase(Base):
    __tablename__ = "network_interface"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    ipv4 = Column(String)
    ipv6 = Column(String)
    ipv4_type = Column(String)
    ipv6_type = Column(String)
    gateway4 = Column(String)
    gateway6 = Column(String)
    dns = Column(String)
    active = Column(Integer)
    status = Column(Integer)


class NetworkServiceBase(Base):
    __tablename__ = "network_service_access"
    id = Column(Integer, primary_key=True)
    protocol = Column(Text)
    port_from = Column(Integer)
    port_to = Column(String)
    interface_id = Column(Integer, ForeignKey("network_interface.id"))
    interface_name = Column(Text)


class NetworkStaticRouteBase(Base):
    __tablename__ = "network_static_route"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    destination = Column(String)
    netmask = Column(Integer)
    gateway = Column(String)
    metric = Column(Integer)
    interface = Column(String)
    active = Column(Integer)
    type = Column(Integer)


class ScanResultDetailBase(Base):
    __tablename__ = "scan_result_detail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vulnerability_name = Column(String)
    description = Column(String)
    history_id = Column(Integer, ForeignKey("scan_web_history.id"), nullable=True)
    scan_web_history = relationship("ScanHistoryBase", backref=backref("scan_web_history", uselist=True))


class ScanScheduleBase(Base):
    __tablename__ = "scan_web_schedule"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_in = Column(Date)
    period_id = Column(Integer, ForeignKey("object_period.id"), nullable=True)
    mail_sender_id = Column(Integer, ForeignKey("object_mail_sender.id"), nullable=True)
    object_period = relationship("PeriodBase", backref=backref("object_period_schedule", uselist=True))
    object_mail_sender = relationship("MailSenderBase", backref=backref("object_mail_sender_schedule", uselist=True))


class ScanHistoryBase(Base):
    __tablename__ = "scan_web_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    datetime = Column(DateTime)
    website = Column(String)
    status = Column(Integer)
    scan_type = Column(String)
    total_vulner = Column(Integer)
    ip = Column(String)
    system_detail = Column(String)


class SSLBase(Base):
    __tablename__ = "object_ssl"
    id = Column(Integer, primary_key=True)
    ssl_name = Column(String)
    ssl_description = Column(String)
    ssl_key = Column(String)
    ssl_cert = Column(String)


class UserBase(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String)
    password = Column(String)
    phone_number = Column(String)
    full_name = Column(String)
    sex = Column(String)
    date_of_birth = Column(DateTime)
    date_create = Column(DateTime)
    image_link = Column(String)
    email = Column(String)
    can_edit = Column(Integer)
    secret_key = Column(String)
    two_fa_status = Column(Integer)
    ip_conn = Column(Integer)
    last_login_at = Column(DateTime)
    state_login = Column(Integer)


class VulnerabilitiesBase(Base):
    __tablename__ = "scan_web_vulnerability"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    part = Column(String)


# class WAFGroupRuleBase(Base):
#     __tablename__ = "waf_group_rule"
#     id = Column(Integer, primary_key=True)
#     tag = Column(String)
#     name = Column(String)
#     description = Column(String)

class RestoreVersion(Base):
    __tablename__ = "restore_version"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    mode = Column(String)
    description = Column(String)
    file_path = Column(String)
    datetime = Column(String)

class WebsiteBase(Base):
    __tablename__ = "object_website"
    id = Column(Integer, primary_key=True)
    website_domain = Column(String)
    cache = Column(Integer)
    active = Column(Integer)
    ssl_id = Column(Integer, ForeignKey("object_ssl.id"), nullable=True)
    group_website_id = Column(Integer, ForeignKey("object_group_website.id"), nullable=True)
    website_status = Column(Integer)
    health_check_status = Column(Integer)
    listen = relationship("WebsiteListenBase")
    upstream = relationship("WebsiteUpstreamBase")
    object_exception = relationship("ExceptionBase", back_populates="object_website")

class WebsiteListenBase(Base):
    __tablename__ = "website_listen"
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("object_website.id"))
    redirect = Column(String)
    main = Column(Integer)
    protocol = Column(String)
    ssl = Column(Integer)


class WebsiteUpstreamBase(Base):
    __tablename__ = "website_upstream"
    id = Column(Integer, primary_key=True)
    website_id = Column(Integer, ForeignKey("object_website.id"))
    ip = Column(String)
    port = Column(Integer)
    type = Column(String)
    protocol = Column(String)
    ssl = Column(Integer)
    object_website = relationship("WebsiteBase", backref=backref("object_website_upstream", uselist=True))


# class WAFRuleStatusBase(Base):
#     __tablename__ = "waf_rule_status"
#     group_website_id = Column(Integer, ForeignKey("object_group_website.id"), primary_key=True)
#     group_rule_id = Column(Integer, ForeignKey("waf_group_rule.id"), primary_key=True)
#     rule_status = Column(Integer)


class SMSSenderBase(Base):
    __tablename__ = "object_sms_sender"
    id = Column(Integer, primary_key=True)
    sms_sender_name = Column(String)


class AlertTypeBase(Base):
    __tablename__ = "alert_type"
    id = Column(Integer, primary_key=True)
    type_name = Column(String)


class WAFAlertBase(Base):
    __tablename__ = "waf_alert"
    id = Column(Integer, primary_key=True)
    alert_type_id = Column(Integer, ForeignKey("alert_type.id"))
    barrier = Column(Integer)
    interval_time = Column(Integer)
    mail_sender_id = Column(Integer, ForeignKey("object_mail_sender.id"), nullable=True)
    sms_sender_id = Column(Integer, ForeignKey("object_sms_sender.id"), nullable=True)
    status = Column(Integer)
    group_website_id = Column(Integer, ForeignKey("object_group_website.id"))


class WAFAlertAccountBase(Base):
    __tablename__ = "waf_alert_has_account"
    waf_alert_id = Column(Integer, ForeignKey("waf_alert.id"), primary_key=True)
    account_id = Column(Integer, ForeignKey("object_account.id"), primary_key=True)
    object_account = relationship("AccountBase", backref=backref("object_account_waf", uselist=True))


class SNMPCommunityBase(Base):
    __tablename__ = "snmp_community"
    id = Column(Integer, primary_key=True)
    enable = Column(Integer)
    community_version = Column(Integer)
    community_name = Column(String)
    community_hosts = Column(String(64000))
    security_level = Column(String(64000))
    queries = Column(String(64000))
    traps = Column(String(64000))
    snmp_events = Column(String(64000))


class WebLimitBandwidthBase(Base):
    __tablename__ = "web_limit_bandwidth"
    id = Column(Integer, primary_key=True)
    sum_conn = Column(Integer)
    site_conn = Column(Integer)
    limit_rate_after = Column(Integer)
    limit_rate = Column(Integer)
    name = Column(String)
    status = Column(Integer)
    website_id = Column(Integer, ForeignKey("object_website.id"), nullable=True)


class LimitBandwidthHaveUrlBase(Base):
    __tablename__ = "limit_bandwidth_have_url"
    bandwidth_id = Column(Integer, ForeignKey("web_limit_bandwidth.id"), primary_key=True)
    url_id = Column(Integer, ForeignKey("ddos_application_layer_uri.id"), primary_key=True)

class RuleAvailableBase(Base):
    __tablename__ = "object_rule_available"
    id = Column(Integer, primary_key=True)
    rule_available_name = Column(String)
    rule_available_status = Column(Integer)

class CRSBase(Base):
    __tablename__ = "object_crs_rule"
    id = Column(Integer, primary_key=True)
    id_rule = Column(String)
    description = Column(String)
    message = Column(String)
    tag = Column(String)
    rule_available_id= Column(Integer, ForeignKey("object_rule_available.id"), nullable=True)
    rule_detail = Column(String)
    path_file = Column(String)
    
class TrustwaveBase(Base):
    __tablename__ = "object_trustwave_rule"
    id = Column(Integer, primary_key=True)
    id_rule = Column(String)
    message = Column(String)
    tag = Column(String)
    rule_available_id = Column(Integer, ForeignKey("object_rule_available.id"), nullable=True)
    rule_detail = Column(String)

class RuleOtherBase(Base):
    __tablename__ = "object_rule_other"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    rule_other_status = Column(Integer)


class RuleOtherDetailBase(Base):
    __tablename__ = "rule_other_detail"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_rule = Column(String)
    rules = Column(String)
    description = Column(String)
    waf_rule_id = Column(Integer, ForeignKey("object_rule_other.id"), nullable=True)
    message = Column(String)
    tag = Column(String)
    path_rule=Column(String)
    
class ExceptionBase(Base):
    __tablename__ = "object_exception"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_rule = Column(String)
    rules = Column(String)
    description = Column(String)
    excep_status = Column(Integer)
    website_id = Column(Integer, ForeignKey("object_website.id"))
    object_website = relationship("WebsiteBase", back_populates="object_exception")
    sites = Column(String)

class GroupWebsiteHaveCRS(Base):
    __tablename__ = "group_website_have_crs"
    group_website_id = Column(Integer, ForeignKey("object_group_website.id"), primary_key=True, nullable=True)
    crs_id = Column(Integer, ForeignKey("object_crs_rule.id"), primary_key=True, nullable=True)
    group_rule_status = Column(Integer)
    object_group_website = relationship("GroupWebsiteBase", backref=backref("object_group_website_has_crs"), uselist=True)
    object_crs = relationship("CRSBase", backref=backref("crs_has_group_website"), uselist=True)

class GroupWebsiteHaveTrustwave(Base):
    __tablename__ = "group_website_have_trustwave"
    group_website_id = Column(Integer, ForeignKey("object_group_website.id"), primary_key=True, nullable=True)
    trustwave_id = Column(Integer, ForeignKey("object_trustwave_rule.id"), primary_key=True, nullable=True)
    group_rule_status = Column(Integer)
    object_group_website = relationship("GroupWebsiteBase", backref=backref("object_group_website_has_trustwave"), uselist=True)
    object_trustwave = relationship("TrustwaveBase", backref=backref("trustwave_has_group_website"), uselist=True)


class GroupWebsiteHaveRuleOther(Base):
    __tablename__ = "group_website_have_rule_other"
    group_website_id = Column(Integer, ForeignKey("object_group_website.id"), primary_key=True, nullable=True)
    rule_other_id = Column(Integer, ForeignKey("rule_other_detail.id"), primary_key=True, nullable=True)
    group_rule_status = Column(Integer)
    object_group_website = relationship("GroupWebsiteBase", backref=backref("object_group_website_has_rule_other"), uselist=True)
    rule_other_detail = relationship("RuleOtherDetailBase", backref=backref("rule_has_group_website"), uselist=True)


class WebsiteHaveCRS(Base):
    __tablename__ = "website_have_crs"
    website_id = Column(Integer, ForeignKey("object_website.id"), primary_key=True, nullable=True)
    crs_id = Column(Integer, ForeignKey("object_crs_rule.id"), primary_key=True, nullable=True)
    rule_status = Column(Integer)
    object_website = relationship("WebsiteBase", backref=backref("object_website_has_crs"), uselist=True)
    object_crs = relationship("CRSBase", backref=backref("crs_has_website"), uselist=True)


class WebsiteHaveTrustwave(Base):
    __tablename__ = "website_have_trustwave"
    website_id = Column(Integer, ForeignKey("object_website.id"), primary_key=True, nullable=True)
    trust_id = Column(Integer, ForeignKey("object_trustwave_rule.id"), primary_key=True, nullable=True)
    rule_status = Column(Integer)
    object_website = relationship("WebsiteBase", backref=backref("object_website_has_trustwave"), uselist=True)
    object_trustwave = relationship("TrustwaveBase", backref=backref("trustwave_has_website"), uselist=True)


class WebsiteHaveRuleOther(Base):
    __tablename__ = "website_have_rule_other"
    website_id = Column(Integer, ForeignKey("object_website.id"), primary_key=True, nullable=True)
    rule_other_id = Column(Integer, ForeignKey("rule_other_detail.id"), primary_key=True, nullable=True)
    rule_status = Column(Integer)
    object_website = relationship("WebsiteBase", backref=backref("object_website_has_rule_other"), uselist=True)
    rule_other_detail = relationship("RuleOtherDetailBase", backref=backref("rule_has_website"), uselist=True)
    
class AntiVirusBase(Base):
    __tablename__ = "object_anti_virus"
    id = Column(Integer, primary_key=True)
    id_rule = Column(String)
    msg = Column(String)
    tag = Column(String)
    description = Column(String)
    name = Column(String)
    
class AntiVirusHaveGroupWebsite(Base):
    __tablename__ = "anti_virus_have_group_website"
    anti_id = Column(Integer, ForeignKey("object_anti_virus.id"), primary_key=True, nullable=True)
    group_website_id = Column(Integer, ForeignKey("object_group_website.id"), primary_key=True, nullable=True)
    group_rule_status = Column(Integer)
    object_group_website = relationship("GroupWebsiteBase", backref=backref("object_group_website_has_anti_virus"), uselist=True)
    object_anti_virus = relationship("AntiVirusBase", backref=backref("anti_have_group_website"), uselist=True)

class AntiVirusHaveWebsite(Base):
    __tablename__ = "website_have_anti"
    anti_id = Column(Integer, ForeignKey("object_anti_virus.id"), primary_key=True, nullable=True)
    website_id = Column(Integer, ForeignKey("object_website.id"), primary_key=True, nullable=True)
    rule_status = Column(Integer)
    object_website = relationship("WebsiteBase", backref=backref("website_has_anti_virus"), uselist=True)
    object_anti_virus = relationship("AntiVirusBase", backref=backref("anti_have_website"), uselist=True)

class ActiveHealthCheckBase(Base):
    __tablename__ = "active_health_check"
    id = Column(Integer, primary_key=True, nullable=True)
    size = Column(Integer)
    url = Column(String)
    port_check = Column(String)
    interval = Column(Integer)
    timeout = Column(Integer)
    fall = Column(Integer)
    rise = Column(Integer)
    valid_statuses = Column(String)
    concurrency = Column(Integer)
    website_id = Column(Integer, ForeignKey("object_website.id"))
    object_website = relationship("WebsiteBase", backref=backref("object_health_check"), uselist=True)
    
class SessionManagerBase(Base):
    __tablename__ = 'session_manager'
    id = Column(Integer, primary_key=True, nullable=True)
    jti_access = Column(String)
    exp_access = Column(Integer)
    ip_address = Column(String)
    login_time = Column(DateTime)
    account = Column(String)
    jti_refresh= Column(String)
    exp_refresh = Column(Integer)

class StorageBase(Base):
    __tablename__ = 'log_storage'
    id = Column(Integer, primary_key=True, nullable=True)
    system_log_time = Column(String)
    system_file_size = Column(Integer)
    waf_log_time = Column(String)
    waf_file_size = Column(Integer)