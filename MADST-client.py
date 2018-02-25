import socket
import win32event
import win32service
import win32serviceutil
import requests
from Cryptodome.Cipher import AES
import base64
from pyad import adbase, adcomputer, adcontainer, adsearch, adquery, addomain, pyad, aduser, adgroup, pyadexceptions
import time
import argparse
import sys
from decorators import *

try:
	import config
except ImportError:
	print("Failed to import config, please ensure the example is copied to config.py.")
	sys.exit(1)

class MADST_Client(object):


	_svc_name_ = "MADST Client"
	_svc_display_name_ = "MADST Client"

	def __init__(self, *args):
#		win32serviceutil.ServiceFramework.__init__(self, *args)
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
		socket.setdefaulttimeout(60)

		self.updated_users = 0
		self.added_users = 0

		parser = argparse.ArgumentParser(description='MADST Client', prog='MADST-client')
		parser.add_argument('-d', '--dry-run', help='Shows you what actions would be taken', action='store_true')
		parser.add_argument('--test', help='enables test functionality', action='store_true')
		pargs = parser.parse_args()
		if pargs.test:
			print("Running in test mode.")
		self.test = pargs.test
		self.dry_run = pargs.dry_run

	def get_ou(self, ou):
		try:
			return adcontainer.ADContainer.from_dn(ou)
		except pywintypes.com_error:
			raise

	def update_password(self, cn, password):
		user = aduser.ADUser.from_cn(cn)
		user.set_password(password)

	def add_ad_user(self, ou, cn, single_attributes=None, multi_attributes=None):
		''' Creates a new user in the designated OU '''
		ou.create_user(cn)
		user = aduser.ADUser.from_cn(cn)
		user.update_attributes(single_attributes)
		for key, value in multi_attributes.items():
			if key == 'memberOf':
				for dn in value:
					group = adgroup.ADGroup.from_dn(dn)
					group.add_members(user)
			else:
				user.append_to_attribute(key, value)

	def disable_user(self, cn):
		user = aduser.ADUser.from_cn(cn)
		user.disable()

	def enable_user(self, cn):
		user = aduser.ADUser.from_cn(cn)
		user.enable()


	def check_user_exists(self, cn):
		""" Returns True if you are trying to create an existing CN """
		try:
			user = aduser.ADUser.from_cn(cn)
		except pyad.invalidResults:
			return False
		except:
			raise
		if user:
			return True

	def decrypt(string, pkey):
		cipher = AES.new(pkey, AES.MODE_ECB)
		passout = cipher.decrypt(base64.b64decode(string))
		return passout.strip()

	@apiAuth
	def change_task_status(task_id, status_id):
		requests.put(config.host + 'api/task/'+str(task_id), params={'apikey': config.apikey, 'secret': config.private_key}, json={'status': status_id})

	def count_billable_cn(self):
		r = get_count_dn()
		billable_group = r['billable_group']
		l = adgroup.ADGroup(distinguished_name=billable_group).get_members(recursive=True)
		count=0
		for item in l:
			count +=1
		update_count(count)

	@apiAuth
	def get_count_dn(self):
		r = requests.get(
			config.host + 'api/org/users/count',
			params={
				'apikey': config.apikey,
				'secret': config.private_key,
				'org_id': config.org_id
			}
		)
		return r

	@apiAuth
	def update_count(self, count):
		r = requests.put(
			config.host + 'api/org/users/count',
			params={
				'apikey': config.apikey,
				'secret': config.private_key,
				'org_id': config.org_id
			},
			json={'billable_users': count}
		)
		return r

	@apiAuth
	def task_check(self):
		params = {'apikey': config.apikey, 'secret': config.private_key, 'org_id': config.org_id}
		return requests.get(config.host + 'api/tasks', params=params)



	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)

	def SvcDoRun(self):
		while True:
			for key, value in self.task_check().items():
				if value['status']['id'] == 1:
					if value['type'] == 'create':
						cn = value['user']['first_name'] + ' ' + value['user']['last_name']
						password = value['user']['sync_password']
						password = decrypt(password.encode('utf-8'), config.private_key.encode('utf-8')).decode('utf-8')
						if self.check_user_exists(cn) is True:
							try:
								self.update_password(cn, password)
								print('Updated User {}'.format(cn))
								self.change_task_status(value['id'], '3')
								print("Task {} changed to status {}".format(value['id'], '3'))
							except:
								self.change_task_status(value['id'], '4')
								print("Task {} changed to status {}".format(value['id'], '4'))
						else:
							# User doesn't exist, create them
							try:
								if not self.test:
									try:
										self.add_ad_user(get_ou(value['organization']['admin_ou']), cn, single_attributes=value['attributes']['single_attributes'], multi_attributes=value['attributes']['multi_attributes'])
									except pyadexceptions.InvalidAttribute:
										self.change_task_status(value['id'], '5')
										print("Task {} changed to status {}".format(value['id'], '5'))
										raise
									self.update_password(cn, password)
									print('Added User {}'.format(cn))
									self.added_users = self.added_users + 1
									self.change_task_status(value['id'], '3')
									print("Task {} changed to status {}".format(value['id'], '3'))
								elif self.test:
									print("Would have added user {} to ou {} with {} single attributes, and {} multi attributes.".format(cn, value['organization']['admin_ou'], value['attributes']['single_attributes'], value['attributes']['multi_attributes']))
									print("Would have changed task id {} to status {}".format(value['id'], '3'))
							except:
								if not value['id']['status']['id'] == 5:
									self.change_task_status(value['id'], '4')
									print("Task {} changed to status {}".format(value['id'], '4'))
								print("Failed to add user {} in ou {}".format(cn, value['organization']['admin_ou']))
								raise
					if value['type'] == 'disable':
						cn = value['user']['first_name'] + ' ' + value['user']['last_name']
						try:
							self.disable_user(cn)
							self.change_task_status(value['id'], '3')
							print("Task {} changed to status {}".format(value['id'], '3'))
						except:
							self.change_task_status(value['id'], '4')
							print("Task {} changed to status {}".format(value['id'], '4'))
					if value['type'] == 'enable':
						cn = value['user']['first_name'] + ' ' + value['user']['last_name']
						try:
							self.enable_user(cn)
							self.change_task_status(value['id'], '3')
							print("Task {} changed to status {}".format(value['id'], '3'))
						except:
							self.change_task_status(value['id'], '4')
							print("Task {} changed to status {}".format(value['id'], '4'))
				else:
					print('No new issues')
			self.count_billable_cn()
			# if self.added_users:
			# 	print("Added {} users".format(self.added_users))
			# if self.updated_users:
			# 	print("Updated {} users".format(self.updated_users))
			time.sleep(5)

if __name__ == '__main__':
	run = MADST_Client(sys.argv)
	run.SvcDoRun()

#if __name__ == '__main__':
#	if len(sys.argv) == 1:
#		servicemanager.Initialize()
#		servicemanager.PrepareToHostSingle(MADST_Client)
#		servicemanager.StartServiceCtrlDispatcher()
#	else:
#		win32serviceutil.HandleCommandLine(MADST_Client)