from app.libraries.http.response import get_status_code_200
import copy

FACILITY_COLLECTIONS = {
    "kern": {
        "name": "Kern",
        "description": "kernel messages"
    },
    "user": {
        "name": "User",
        "description": "user-level messages"
    },
    "syslog": {
        "name": "Syslog",
        "description": "messages generated internally by syslogd"
    },
    "local0": {
        "name": "local0",
        "description": "local use 0 (local0)"
    },
    "local1": {
        "name": "local1",
        "description": "local use 1 (local1)"
    }
}

SEVERITY_COLLECTIONS = {
    "crit": {
        "name": "Critical",
        "description": "critical conditions"
    },
    "error": {
        "name": "Error",
        "description": "error conditions"
    },
    "warning": {
        "name": "Warning",
        "description": "warning conditions"
    },
    "info": {
        "name": "Informational",
        "description": "informational messages"
    },
    "debug": {
        "name": "Debug",
        "description": "debug-level messages"
    }
}

LOG_TYPE_COLLECTIONS = {
    "modsecurity_log": {
        "file": "/var/log/nginx/modsec_audit.log",
        "name": "Modsecurity Log",
        "description": "Modsecurity Log",
    },
    "nginx_error_log": {
        "file": "/var/log/nginx/error.log",
        "name": "Nginx Error Log",
        "description": "Nginx Error Log"
    },
    "nginx_access_log": {
        "file": "/var/log/nginx/access.log",
        "name": "Nginx Access Log",
        "description": "Nginx Access Log"
    },
    "iptables_log": {
        "file": "/var/log/iptables.log",
        "name": "iptables Log",
        "description": "iptables Log"
    },
    "syslog": {
        "file": "/var/log/syslog",
        "name": "Syslog",
        "description": "Syslog"
    },
    "kern": {
        "file": "/var/log/kern.log",
        "name": "Kernel Log",
        "description": "Kernel Log"
    }
}


class LogForwardCollections(object):
    def syslog_collections(self):
        pass

    def snmp_collections(self):
        return self.log_type()

    def log_type(self):
        log_type_collect = copy.deepcopy(LOG_TYPE_COLLECTIONS)
        for log_type in log_type_collect:
            del log_type_collect[log_type]["file"]
        return get_status_code_200(log_type_collect)

    def facility_collections(self):
        return get_status_code_200(FACILITY_COLLECTIONS)

    def severity_collections(self):
        return get_status_code_200(SEVERITY_COLLECTIONS)
