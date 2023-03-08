from app.libraries.data_format.validate_data import is_ipv4, is_ipv6, is_domain, is_port
from app.libraries.http.response import status_code_400, status_code_200
from app.libraries.logger import c_logger
from app.libraries.system.log_action import log_setting
from app.libraries.system.shell import check_open_port


class Diagnostic(object):
    def __init__(self):
        self.logger = c_logger("diagnostic")

    def ping(self, ping_json):
        from pythonping import ping

        def verify_input(json):
            verify = ""
            if "ip_address" in json:
                if not is_ipv4(json["ip_address"]) and not is_ipv6(json["ip_address"]) \
                        and not is_domain(json["ip_address"]):
                    verify += f"not validate ip {json['ip_address']} "
            if "count" in json:
                if not str(json["count"]).isdigit():
                    verify += "count not validate, "
            else:
                json["count"] = 4

            if "packet_size" in json:
                if not str(json["packet_size"]).isdigit():
                    verify += "packet_size not validate, "
            else:
                json["packet_size"] = 64

            if "timeout" in json:
                if not str(json["timeout"]).isdigit():
                    verify += "timeout not validate, "
            else:
                json["timeout"] = 800

            return verify

        error_code = verify_input(ping_json)
        if error_code != "":
            self.logger.log_writer.error(error_code)
            return status_code_400("ping.fail.client")

        result = ping(ping_json["ip_address"], verbose=False,
                      size=ping_json["packet_size"], count=ping_json["count"],
                      timeout=ping_json["timeout"])
        packet = []
        for response in result._responses:
            _tmp = str(response).split(" ")
            res = {
                "seq": 1,
                "reply_from": _tmp[2],
                "packet_size": _tmp[3],
                "time": _tmp[6],
                "TTL": 128
            }
            packet.append(res)
        output = {
            "ping_packet": packet,
            "time": {
                "min": result.rtt_min_ms,
                "max": result.rtt_max_ms,
                "avg": result.rtt_avg_ms
            }
        }
        return status_code_200("ping.success", output)

    def trace_route(self, trace_route_json):
        from app.libraries.system.shell import run_command

        def verify_input(json):
            verify = ""
            if "ip_address" in json:
                if not is_ipv4(json["ip_address"]) and not is_ipv6(json["ip_address"]) \
                        and not is_domain(json["ip_address"]):
                    verify += f"not validate ip {json['ip_address']} "
            else:
                verify += "missing ip address, "
            if "max_ttl" in json:
                if not str(json["max_ttl"]).isdigit():
                    verify += "ttl not validate, "
            else:
                json["max_ttl"] = 30
            return verify

        error_code = verify_input(trace_route_json)
        if error_code != "":
            self.logger.error(error_code)
            return status_code_400("traceroute.fail.client")
        result = run_command(f"traceroute -m {trace_route_json['max_ttl']} -n {trace_route_json['ip_address']}")
        result = result.decode("utf-8").split("\n")

        first_line = result[0].strip().split(" ")
        trace_to = first_line[2]
        real_ip = first_line[3]

        base_response = {
            "traceroute_packet": [],
            "trace_to": trace_to,
            "real_ip": real_ip
        }
        for line in result[1:-1]:
            _tmp = line.strip().split(" ")
            seq = int(_tmp[0])
            ip = _tmp[2]
            if ip != "*":
                value = []
                for i in range(3, len(_tmp)):
                    if _tmp[i] == "ms":
                        value.append(f"{_tmp[i - 1]} ms")
                    if _tmp[i] == "*":
                        value.append(_tmp[i])
            else:
                ip = None
                value = ["*", "*", "*"]
            data = {
                "seq": seq,
                "time": value,
                "reply_from": ip
            }
            base_response["traceroute_packet"].append(data)
        monitor_setting = log_setting(action="Diagnostic", status=1,
                                      description=f"Trace route {trace_route_json['ip_address']}")
        return status_code_200("traceroute.success", base_response)

    def port_check(self, port_check_json):
        def verify_input(json):
            verify = ""
            if "ip_address" in json:
                if not is_ipv4(json["ip_address"]) and not is_ipv6(json["ip_address"]) \
                        and not is_domain(json["ip_address"]):
                    verify += f"not validate ip {json['ip_address']} "
            else:
                verify += "missing ip address, "
            if "port" in json:
                if not is_port(str(json["port"])):
                    verify += "port not validate, "
            else:
                verify += "port missing, "
            return verify

        error_code = verify_input(port_check_json)
        if error_code != "":
            self.logger.error(error_code)
            return status_code_400("portcheck.fail.client")
        response = check_open_port(port_check_json["ip_address"], int(port_check_json["port"]))
        monitor_setting = log_setting(action="Diagnostic", status=1,
                                      description=f"Port check "
                                                  f"{port_check_json['ip_address']}:{port_check_json['port']}")
        return status_code_200("portcheck.success", response)
