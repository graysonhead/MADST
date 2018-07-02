import json
from json.decoder import JSONDecodeError
import os
from schema import ConfigData
from marshmallow import ValidationError
import sys


class Config(object):
	def __init__(self):

		config_path = os.path.join('C:\\', 'Program Files', 'MADST Client')
		if not os.path.exists(config_path):
			os.makedirs(config_path)
		os.chdir(config_path)
		config_file = 'config.json'
		if len(sys.argv) > 1:
			if sys.argv[1] == 'remove':
				return
		file_loaded = False
		while not file_loaded:
			try:
				data = {}
				with open(config_file, 'r') as config:
					data.update(json.load(config))
				self.host = data['host']
				self.org_id = data['org_id']
				self.apikey = data['apikey']
				self.private_key = data['private_key']
				file_loaded = True
			except (FileNotFoundError, JSONDecodeError, KeyError):
				while self.create_json_file(config_file) is False:
					print('Please try again.')

	def create_json_file(self, path):
		file_data = {
			'host': input("Enter host URI, e.g. 'https://madst.your-domain.com': "),
			'org_id': input("Enter host ID (from the organization page on MADST Server): "),
			'apikey': input("Enter API Key (from the organization page on MADST Server): "),
			'private_key': input("Enter API Password (from the organization page on MADST Server): ")
		}
		try:
			schema = ConfigData(strict=True)
			schema.load(file_data)
			json_data = schema.dumps(file_data).data
			with open(path, 'w') as config:
				config.write(json_data)
			if os.path.isfile(path):
				return True
		except Exception as e:
			print(e)
			return False
