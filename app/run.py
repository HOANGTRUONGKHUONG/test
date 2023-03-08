import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api

# from app.functions.rule_config.rule_config_api import NewRuleConfigurationAPI, ExclusionAPI, RemoveRuleAPI, \
# 	NewRuleConfigurationDetailAPI, ExclusionDetailAPI, RemoveRuleDetailAPI
from app.functions.about.about_api import AboutAPI
from app.functions.backup_restore.backup_restore_api import RestoreAPI, BackupScheduleAPI, RestoreDetailAPI, \
    RestoreDefaultAPI, DownloadBackupFile, CheckStatus, BackupNow
from app.functions.ddos.ddos_application_layer.URI.ddos_application_layer_uri_api import DDosApplicationURIAPI, \
    DDosApplicationURIDetailAPI
from app.functions.ddos.ddos_application_layer.rules.config_rule_api import ConFigRuleAPI, ConFigRuleDetailAPI
from app.functions.ddos.ddos_network_layer.ddos_network_layer_api import DDosNetworkLayerAPI, DDosNetworkLayerDetailAPI
from app.functions.diagnostic.diagnostic_api import PingAPI, TraceRouteAPI, PortCheckAPI
from app.functions.high_availability.high_availability_api import HighAvailabilityAPI, HighAvailabilityModeAPI
from app.functions.licence.licence_api import LicenceAPI, VersionCheckAPI, VersionDownloadAPI, VersionUpdateAPI
from app.functions.log_forward.snmp.snmp_api import SNMPConfigAPI, SNMPCollectionsAPI, SNMPCommunityAPI, \
    SNMPCommunityDetailAPI, SNMP3CommunityAPI, SNMP3CommunityDetailAPI
from app.functions.log_forward.syslog.syslog_api import SyslogAPI, FacilityAPI, SeverityAPI, LogTypeAPI, SyslogTestAPI
from app.functions.login.login_api import LoginAPI, LogoutAccessAPI, LogoutRefreshAPI, RefreshAccessTokenAPI, \
	TwoFactorAuthentication
from app.functions.monitors.connection.monitor_connection_api import MonitorConnectionAPI, MonitorWebsiteConnectAPI, \
	MonitorIPConnectAPI
from app.functions.monitors.ddos.monitor_ddos_api import MonitorDdosAppAPI, MonitorDdosNetAPI, \
    MonitorDDoSChartCountAPI, MonitorDDoSChartAPI, MonitorDDosAppDownload, MonitorDDosNetDownload, UnlockNetIPAPI, \
    UnlockAppIPAPI
from app.functions.monitors.http_status.monitor_http_status_api import MonitorHTTPStatusAPI
from app.functions.monitors.resource.monitor_resource_api import MonitorResourceAPI
from app.functions.monitors.setting.monitor_setting_api import MonitorSettingAPI
from app.functions.monitors.traffic.monitor_traffic_api import MonitorTrafficAPI
from app.functions.monitors.waf.monitor_waf_api import MonitorWAFAPI, MonitorWAFChartAPI, MonitorWAFChartCountAPI, \
	MonitorWAFDownload
from app.functions.network.network_api import VirtualNetworkBondAPI, \
	VirtualNetworkBridgesAPI, VirtualNetworkBridgesDetailAPI, VirtualNetworkBondDetailAPI
from app.functions.network.network_api import NetworkAPI, NetworkDetailAPI, PhysicalInterfaceAPI, VirtualInterfaceAPI
from app.functions.objects.account.account_api import AccountAPI, AccountDetailAPI
from app.functions.objects.group_website.group_website_api import GroupWebsiteAPI, GroupWebsiteDetailAPI
from app.functions.objects.ip.black_list_api import BlackListAPI, BlackListDetailAPI
from app.functions.objects.ip.white_list_api import WhiteListAPI, WhiteListDetailAPI
from app.functions.objects.mail_sender.mail_sender_api import MailSenderAPI, MailSenderDetailAPI
from app.functions.objects.mail_server.mail_server_api import MailServerAPI
from app.functions.objects.report.report_api import ReportAPI, PeriodAPI, ReportDetailAPI, HtmlFormAPI
from app.functions.objects.secure_sockets_layer.ssl_api import SSLAPI, SSLDetailAPI
from app.functions.objects.sms_sender.sms_sender_api import SMSSenderAPI
from app.functions.objects.website.website_api import WebsiteAPI, WebsiteDetailAPI, ClearCachingAPI
from app.functions.service.service_api import ServiceAPI, ServiceDetailAPI
from app.functions.system_status.system_status_api import SystemStatusAPI
from app.functions.system_time.system_time_api import SystemTimeAPI, SystemNTPTimeAPI, TimezoneAPI
from app.functions.user.user_api import UserDetailAPI, UserAPI, ProfileAPI, PasswordAPI
from app.functions.waf.waf_api import WebApplicationFirewallAPI, WebApplicationFirewallDetailAPI, \
    WebApplicationFirewallAlert, WAFWebsiteAPI, WebApplicationFirewallRuleAPI, WebApplicationFirewallRuleDetail, \
    WebsiteWAFRuleAPI, WebsiteWAFRuleDetail, WAFDropDownAPI
from app.functions.waf.exception_api import WAFExceptionAPI, WAFExceptionDetailAPI
from app.functions.waf.site_api import WAFSiteAPI
from app.functions.web_scans_vulnerabilities.History_scan.web_scans_history_api import WebHistoryAPI, HistoryInformAPI
from app.functions.web_scans_vulnerabilities.current_scan.web_scans_vulnerabilities_api import WebScansAPI, \
    ScanVulnerabilityAPI, LogFile, WebScanDetailAPI, DownloadLogfile
from app.functions.web_scans_vulnerabilities.schedule_scan.web_scans_schedule_api import WebScheduleAPI, \
    WebScheduleDetailAPI
from app.functions.route.route_api import RouteAPI, RouteDetailAPI
from app.functions.objects.rule_management.rule_available.rule_available_api import RuleAvailableAPI, RuleAvailableDetailAPI
from app.functions.objects.rule_management.rule_available.crs_api import CRSRuleAPI, CRSRuleDetailAPI, DownloadCRSRule
from app.functions.objects.rule_management.rule_available.trustwave_api import TrustwaveRuleAPI, TrustwaveRuleDetailAPI, DownloadTrustwaveRule
from app.functions.objects.rule_management.rule_other.rule_other_api import RuleOtherAPI, RuleOtherDetailAPI, DownloadRuleOther, UploadRuleOther
from app.functions.objects.rule_management.rule_other.rule_waf_api import WafRuleAPI, WafRuleDetailAPI

from app.functions.antivirus.antivirus_api import AntivirusAPI,DownloadFileScannedAPI
from app.functions.setting.limit_conn.limit_conn_api import LimitAPI
from app.functions.setting.token.token_time_api import TokenAPI
from app.functions.setting.manager_session.manager_session_api import SessionAPI, SessionDetailAPI
from app.functions.log_setting.log_storage_api import StorageAPI

from app.libraries.ORMBase import ORMSession_alter
from app.model import DeadTokenBase, UserBase
from app.setting import ACCESS_TOKEN_TIME, REFRESH_TOKEN_TIME

app = Flask(__name__)
CORS(app)
sc_key = str(os.urandom(64))
app.config['JWT_SECRET_KEY'] = "sc_key"
jwt = JWTManager(app)
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(ACCESS_TOKEN_TIME)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(REFRESH_TOKEN_TIME)
# app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 1800
# app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 3600
# app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 120
# app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 300
api = Api(app)


@jwt.token_in_blacklist_loader
def check_if_token_in_black_list(decrypted_token):
    session,engine_connect = ORMSession_alter()
    jti = decrypted_token['jti']
    query = session.query(DeadTokenBase).filter(DeadTokenBase.token.__eq__(jti)).all()
    if len(query):
        return True
    return False


@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    session,engine_connect = ORMSession_alter()
    user_detail = session.query(UserBase).filter(UserBase.id.__eq__(identity)).first()
    session.close()
    engine_connect.dispose()
    if user_detail.user_name == 'admin':
        roles_name = "admin"
    else:
        if user_detail.can_edit == 1:
            roles_name = "editable"
        else:
            roles_name = "viewable"
    return {"roles": roles_name}


# Interface
api.add_resource(NetworkAPI, "/api/interface", methods=["GET"])
api.add_resource(PhysicalInterfaceAPI, "/api/physical-interface", methods=["OPTIONS"])
api.add_resource(VirtualInterfaceAPI, "/api/virtual-interface", methods=["OPTIONS"])
api.add_resource(NetworkDetailAPI, "/api/interface/<string:interface_name>", methods=["GET", "PUT", "DELETE"])
# Virtual Interface
api.add_resource(VirtualNetworkBondAPI, "/api/virtual-interface/bond", methods=["GET", "POST"])
api.add_resource(VirtualNetworkBridgesAPI, "/api/virtual-interface/bridges", methods=["GET", "POST"])
api.add_resource(VirtualNetworkBridgesDetailAPI, "/api/virtual-interface/bridges/<string:bridges_name>",
                 methods=["GET", "PUT", "DELETE"])
api.add_resource(VirtualNetworkBondDetailAPI, "/api/virtual-interface/bond/<string:bond_name>",
                 methods=["GET", "PUT", "DELETE"])
# Service
api.add_resource(ServiceAPI, "/api/services/<string:interface_name>", methods=["GET", "POST", "OPTIONS"])
api.add_resource(ServiceDetailAPI, "/api/services/<int:service_id>", methods=["GET", "PUT", "DELETE"])
# website
api.add_resource(WebsiteAPI, "/api/website", methods=["GET", "POST"])
api.add_resource(WebsiteDetailAPI, "/api/website/<int:website_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(ClearCachingAPI, "/api/clear-caching/<int:website_id>", methods=["DELETE"])
api.add_resource(GroupWebsiteAPI, "/api/group-website", methods=["GET", "POST"])
api.add_resource(GroupWebsiteDetailAPI, "/api/group-website/<int:group_website_id>",
				 methods=["GET", "PUT", "DELETE", "POST"])
# waf
api.add_resource(WebApplicationFirewallAPI, "/api/waf", methods=["GET"])
api.add_resource(WebApplicationFirewallDetailAPI, "/api/waf/<int:group_website_id>", methods=["GET", "PUT"])
# api.add_resource(WebApplicationFirewallRuleDetail, "/api/waf/<int:group_website_id>/rule/<int:group_rule_id>",
# 				 methods=["GET", "PUT"])

api.add_resource(WebApplicationFirewallRuleAPI, "/api/waf/<int:group_website_id>/rule", methods=["GET"])
api.add_resource(WebApplicationFirewallRuleDetail, "/api/waf/<int:group_website_id>/rule/<int:rule_id>", methods=["PUT"])

api.add_resource(WAFExceptionAPI, "/api/waf/<int:website_id>/exception", methods=["GET", "POST"])
api.add_resource(WAFExceptionDetailAPI, "/api/waf/<int:website_id>/exception/<int:excep_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(WAFWebsiteAPI, "/api/waf_web/<int:website_id>", methods=["PUT"])
api.add_resource(WebsiteWAFRuleAPI, "/api/waf_web/<int:website_id>/rule", methods=["GET"])
api.add_resource(WebsiteWAFRuleDetail, "/api/waf_web/<int:website_id>/rule/<int:rule_id>", methods=["PUT"])
api.add_resource(WAFSiteAPI, "/api/waf/<int:id_rule>/site", methods=["GET", "POST"])
api.add_resource(WAFDropDownAPI, "/api/dropdown_rule", methods=["GET"])

# rule config
# api.add_resource(NewRuleConfigurationAPI, "/api/new-rule", methods=["GET", "POST"])
# api.add_resource(NewRuleConfigurationDetailAPI, "/api/new-rule/<>", methods=["PUT", "DELETE"])
# api.add_resource(RemoveRuleAPI, "/api/remove-rule", methods=["GET", "POST"])
# api.add_resource(RemoveRuleDetailAPI, "/api/remove-rule/<>", methods=["PUT", "DELETE"])
# api.add_resource(ExclusionAPI, "/api/exclusion", methods=["GET", "POST"])
# api.add_resource(ExclusionDetailAPI, "/api/exclusion/<>", methods=["PUT", "DELETE"])
# waf alert
api.add_resource(WebApplicationFirewallAlert, "/api/waf-alert/<int:group_website_id>", methods=["GET", "PUT"])
# ssl
api.add_resource(SSLAPI, "/api/ssl", methods=["GET", "POST"])
api.add_resource(SSLDetailAPI, "/api/ssl/<int:ssl_id>", methods=["GET", "PUT", "DELETE"])
# user
api.add_resource(UserAPI, "/api/user", methods=["GET", "POST"])
api.add_resource(UserDetailAPI, "/api/user/<int:user_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(ProfileAPI, "/api/profile", methods=["GET", "PUT"])
api.add_resource(PasswordAPI, "/api/profile/password", methods=["PUT"])
# login
api.add_resource(LoginAPI, "/api/login", methods=["POST"])
api.add_resource(LogoutAccessAPI, "/api/logout", methods=["DELETE"])
api.add_resource(LogoutRefreshAPI, "/api/logout-token", methods=["DELETE"])
api.add_resource(RefreshAccessTokenAPI, "/api/refresh-token", methods=["GET"])
api.add_resource(TwoFactorAuthentication, "/api/profile/2fa", methods=["POST", "GET", "PUT"])
# ip
api.add_resource(BlackListAPI, "/api/blacklist", methods=["GET", "POST"])
api.add_resource(BlackListDetailAPI, "/api/blacklist/<int:ip_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(WhiteListAPI, "/api/whitelist", methods=["GET", "POST"])
api.add_resource(WhiteListDetailAPI, "/api/whitelist/<int:ip_id>", methods=["GET", "PUT", "DELETE"])
# account
api.add_resource(AccountAPI, "/api/account", methods=["GET", "POST"])
api.add_resource(AccountDetailAPI, "/api/account/<int:account_id>", methods=["GET", "PUT", "DELETE"])
# sms
api.add_resource(SMSSenderAPI, "/api/sms-sender", methods=["GET"])
# mail
api.add_resource(MailSenderAPI, "/api/mail-sender", methods=["GET", "POST"])
api.add_resource(MailSenderDetailAPI, "/api/mail-sender/<int:sender_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(MailServerAPI, "/api/mail-sender/mail-server", methods=["GET"])
# web scan
api.add_resource(LogFile, "/api/web-scan/logfile", methods=["GET"])
api.add_resource(ScanVulnerabilityAPI, "/api/web-scan/vulnerability", methods=["GET"])
api.add_resource(WebScansAPI, "/api/web-scan", methods=["GET", "POST"])
api.add_resource(WebScanDetailAPI, "/api/web-scan/<int:history_id>", methods=["GET", "DELETE"])
api.add_resource(WebScheduleAPI, "/api/scan-schedule", methods=["POST", "GET"])
api.add_resource(WebScheduleDetailAPI, "/api/scan-schedule/<int:schedule_id>", methods=["GET", "DELETE", "PUT"])
api.add_resource(WebHistoryAPI, "/api/scan-history", methods=["GET"])
api.add_resource(HistoryInformAPI, "/api/scan-history/<int:history_id>", methods=["GET"])
api.add_resource(DownloadLogfile, "/api/web-scan/<int:scan_id>/download", methods=["GET"])
# monitor
api.add_resource(UnlockAppIPAPI, "/api/monitor-ddos/application", methods=["PUT"])
api.add_resource(UnlockNetIPAPI, "/api/monitor-ddos/network", methods=["PUT"])
api.add_resource(MonitorDdosNetAPI, "/api/monitor-ddos/network", methods=["GET"])
api.add_resource(MonitorDdosAppAPI, "/api/monitor-ddos/application", methods=["GET"])
api.add_resource(MonitorDDoSChartCountAPI, "/api/monitor-ddos-count", methods=["GET"])
api.add_resource(MonitorDDoSChartAPI, "/api/monitor-ddos-chart", methods=["GET"])
api.add_resource(MonitorDDosAppDownload, "/api/monitor-ddos/application/download", methods=["GET"])
api.add_resource(MonitorDDosNetDownload, "/api/monitor-ddos/network/download", methods=["GET"])
api.add_resource(MonitorResourceAPI, "/api/monitor-resource", methods=["GET"])
api.add_resource(MonitorConnectionAPI, "/api/monitor-connection", methods=["GET"])
api.add_resource(MonitorWebsiteConnectAPI, "/api/website-connection", methods=["GET"])
api.add_resource(MonitorIPConnectAPI, "/api/ip-connection", methods=["GET"])
api.add_resource(MonitorHTTPStatusAPI, "/api/monitor-http-status", methods=["GET"])
api.add_resource(MonitorWAFAPI, "/api/monitor-waf", methods=["GET"])
api.add_resource(MonitorWAFChartAPI, "/api/monitor-waf-chart", methods=["GET"])
api.add_resource(MonitorWAFChartCountAPI, "/api/monitor-waf-count", methods=["GET"])
api.add_resource(MonitorWAFDownload, "/api/monitor-waf/download", methods=["GET"])
api.add_resource(MonitorTrafficAPI, "/api/monitor-traffic", methods=["GET"])
api.add_resource(MonitorSettingAPI, "/api/monitor-system", methods=["GET"])
# high availability
api.add_resource(HighAvailabilityModeAPI, "/api/high-availability-mode", methods=["GET"])
api.add_resource(HighAvailabilityAPI, "/api/high-availability", methods=["GET", "PUT", "POST", "DELETE"])
# licence
api.add_resource(VersionCheckAPI, "/api/update-firmware-check", methods=["GET"])
api.add_resource(VersionDownloadAPI, "/api/update-firmware-download", methods=["GET"])
api.add_resource(VersionUpdateAPI, "/api/update-firmware", methods=["POST"])
api.add_resource(LicenceAPI, "/api/licence", methods=["GET", "POST"])
# about
api.add_resource(AboutAPI, "/api/about", methods=["GET"])
# system_time
api.add_resource(SystemTimeAPI, "/api/system-time", methods=["GET", "POST"])
api.add_resource(SystemNTPTimeAPI, "/api/system-time-ntp", methods=["GET"])
api.add_resource(TimezoneAPI, "/api/timezone", methods=["GET"])
# diagnostic
api.add_resource(PingAPI, "/api/ping", methods=["POST"])
api.add_resource(TraceRouteAPI, "/api/traceroute", methods=["POST"])
api.add_resource(PortCheckAPI, "/api/port-check", methods=["POST"])
# report
api.add_resource(ReportAPI, "/api/report", methods=["GET", "POST"])
api.add_resource(ReportDetailAPI, "/api/report/<int:report_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(PeriodAPI, "/api/period", methods=["GET"])
api.add_resource(HtmlFormAPI, "/api/form", methods=["GET"])
# ddos_network
api.add_resource(DDosNetworkLayerAPI, "/api/ddos-network", methods=["GET"])
api.add_resource(DDosNetworkLayerDetailAPI, "/api/ddos-network/<int:rule_id>", methods=["GET", "PUT"])
# ddos_application
api.add_resource(ConFigRuleAPI, "/api/ddos-application", methods=["GET", "POST"])
api.add_resource(ConFigRuleDetailAPI, "/api/ddos-application/<int:rule_id>", methods=["GET", "PUT", "DELETE"])
# ddos_uri
api.add_resource(DDosApplicationURIAPI, "/api/ddos-application/<rule_id>/uri", methods=["GET"])
api.add_resource(DDosApplicationURIDetailAPI, "/api/ddos-application/<rule_id>/uri/<int:uri_id>", methods=["DELETE"])
# backup_restore
api.add_resource(BackupNow, "/api/backup", methods=["POST"])
api.add_resource(BackupScheduleAPI, "/api/backup-schedule", methods=["GET", "POST"])
api.add_resource(RestoreAPI, "/api/restore", methods=["GET", "POST"])
api.add_resource(RestoreDetailAPI, "/api/restore/<file_id>", methods=["GET", "POST"])
api.add_resource(DownloadBackupFile, "/api/restore/<file_id>/download", methods=["GET"])
api.add_resource(RestoreDefaultAPI, "/api/restore-default", methods=["POST"])
api.add_resource(CheckStatus, "/api/backup-restore-status", methods=["GET"])
# reboot
api.add_resource(SystemStatusAPI, "/api/reboot", methods=["POST"])
# syslog_forward
api.add_resource(SyslogAPI, "/api/logforward", methods=["GET", "POST", "DELETE"])
api.add_resource(FacilityAPI, "/api/facility", methods=["OPTIONS"])
api.add_resource(SeverityAPI, "/api/severity", methods=["OPTIONS"])
api.add_resource(LogTypeAPI, "/api/log-type", methods=["OPTIONS"])
api.add_resource(SyslogTestAPI, "/api/logforward-test", methods=["POST"])
# snmp_forward
api.add_resource(SNMPConfigAPI, "/api/snmp", methods=["GET", "POST"])
api.add_resource(SNMPCollectionsAPI, "/api/snmp-events", methods=["OPTIONS"])
api.add_resource(SNMPCommunityAPI, "/api/snmp-community", methods=["POST"])
api.add_resource(SNMPCommunityDetailAPI, "/api/snmp-community/<string:community_name>",
                 methods=["GET", "PUT", "DELETE"])
api.add_resource(SNMP3CommunityAPI, "/api/snmp-community-v3", methods=["POST"])
api.add_resource(SNMP3CommunityDetailAPI, "/api/snmp-community-v3/<string:community_name>",
                 methods=["GET", "PUT", "DELETE"])
# route
api.add_resource(RouteAPI, "/api/routes", methods=["GET", "POST"])
api.add_resource(RouteDetailAPI, "/api/routes/<int:route_id>", methods=["GET", "PUT", "DELETE"])

# rule_management
# rule_available
api.add_resource(RuleAvailableAPI, "/api/rule_available", methods=["GET"])
api.add_resource(RuleAvailableDetailAPI, "/api/rule_available/<int:rule_available_id>", methods=["GET", "PUT"])

# CRS
api.add_resource(CRSRuleAPI, "/api/rule_available/<int:rule_available_id>/crs_rule", methods=["GET"])
api.add_resource(CRSRuleDetailAPI, "/api/rule_available/<int:rule_available_id>/crs_rule/<int:crs_id>", methods=["GET", "PUT"])
api.add_resource(DownloadCRSRule, "/api/crs/download", methods=["GET"])

# Trustwave
api.add_resource(TrustwaveRuleAPI, "/api/rule_available/<int:rule_available_id>/trustwave_rule", methods=["GET"])
api.add_resource(TrustwaveRuleDetailAPI, "/api/rule_available/<int:rule_available_id>/trustwave_rule/<int:trustwave_id>", methods=["GET", "PUT"])
api.add_resource(DownloadTrustwaveRule, "/api/trustwave/download", methods=["GET"])
# rule_other
api.add_resource(RuleOtherAPI, "/api/waf_rule", methods=["GET", "POST"])
api.add_resource(RuleOtherDetailAPI, "/api/waf_rule/<int:waf_rule_id>", methods=["GET", "PUT", "DELETE"])
api.add_resource(DownloadRuleOther, "/api/waf_rule/<int:waf_rule_id>/download", methods=["GET"])
api.add_resource(UploadRuleOther, "/api/waf_rule/<int:waf_rule_id>/upload", methods=["POST"])
# rule_other_detail
api.add_resource(WafRuleAPI, "/api/waf_rule/<int:waf_rule_id>/rule", methods=["GET", "POST"])
api.add_resource(WafRuleDetailAPI, "/api/waf_rule/<int:waf_rule_id>/rule/<int:rule_id>", methods=["GET", "PUT", "DELETE"])
# antivirus
api.add_resource(AntivirusAPI, "/api/file_scanned", methods=["GET"])
api.add_resource(DownloadFileScannedAPI, "/api/file_scanned/<string:file_name>/download", methods=["GET"])

# token_time
api.add_resource(TokenAPI, "/api/token_time", methods=["GET", "PUT"])

# limit_conn
api.add_resource(LimitAPI, "/api/limit_connection", methods=["GET", "PUT"])

# session_manager
api.add_resource(SessionAPI, "/api/session-management", methods=["GET"])
api.add_resource(SessionDetailAPI, "/api/session-management/<int:id>", methods=["DELETE"])

# log-setting
api.add_resource(StorageAPI, "/api/log-storage", methods=["GET", "PUT"])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
