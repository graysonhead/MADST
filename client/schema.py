from marshmallow import Schema, fields, validates, ValidationError, pre_load
import requests
import re


class ConfigData(Schema):
	host = fields.String(required=True)
	org_id = fields.Integer(required=True)
	apikey = fields.String(required=True)
	private_key = fields.String(required=True)

	@validates('host')
	def check_host(self, url):
		try:
			resp = requests.get('{}admin'.format(url))
		except Exception as e:
			raise ValidationError('Config validation failed; could not contact provide URI: {}'.format(e))

		#todo: perform more meaningful test that 200 response on url so that, e.g. google.com is not accepted
		if not resp.ok:
			raise ValidationError(
				'Config validation failed; provided host did not give the expected response: {}'.format(resp)
			)

	@pre_load
	def correct_input(self, data):
		data['host'] = data['host'].strip()
		data['apikey'] = data['apikey'].strip()
		data['private_key'] = data['private_key'].strip()
		data['host'] = self.host_format_correction(data['host'])
		return data

	def host_format_correction(self, url):
		if not re.match('^http.*', url):
			url = "http://{}".format(url)
		if not re.match('.*/$', url):
			url = '{}/'.format(url)
		print(url)
		return url
