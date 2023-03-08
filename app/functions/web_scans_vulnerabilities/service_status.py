import time

import requests

from app.libraries.system.shell import run_command

if __name__ == '__main__':
	while True:
		try:
			print(requests.get("http://127.0.0.1:1234/version"))
			print("service already Run")
		except Exception as E:
			print(E)
			print(run_command("/home/bwaf/w3af/./w3af_api 127.0.0.1:1234 --no-ssl"))
		time.sleep(300)
