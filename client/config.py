import json
from json import JSONDecodeError
import os


class Config(object):
	def __init__(self):
		data = {}
		config_path = os.path.join('C:\\', 'Program Files', 'MADST Client')
		if not os.path.exists(config_path):
			os.makedirs(config_path)
		os.chdir(config_path)
		config_file = 'config.json'
		try:
			with open(config_file, 'r') as config:
				data.update(json.load(config))
		except FileNotFoundError or JSONDecodeError:
			#todo: marshall this data.
			file_data = {
				'host': input("Enter host URI, e.g. 'https://madst.your-domain.com': "),
				'org_id': input("Enter host ID (from the organization page on MADST Server): "),
				'apikey': input("Enter API Key (from the organization page on MADST Server): "),
				'private_key': input("Enter API Password (from the organization page on MADST Server): ")
			}
			json_data = json.dumps(file_data)
			with open(config_file, 'w') as config:
				config.write(json_data)
		finally:
			with open(config_file, 'r') as config:
				data.update(json.load(config))

		self.host = data['host']
		self.org_id = data['org_id']
		self.apikey = data['apikey']
		self.private_key = data['private_key']
