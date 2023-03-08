from app.libraries.http.response import status_code_200


class SystemStatus(object):
    def __init__(self):
        pass

    def reboot(self, json_data):
        return status_code_200("post.system.reboot.success", {})
