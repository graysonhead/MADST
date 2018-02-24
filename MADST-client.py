import requests
from Cryptodome.Cipher import AES
import base64
from pyad import adbase, adcomputer, adcontainer, adsearch, adquery, addomain, pyad, aduser, adgroup, pyadexceptions
import re
import time
import argparse
import sys
import json
from decorators import *

try:
	import config
except ImportError:
	print("Failed to import config, please ensure the example is copied to config.py.")
	sys.exit(1)


updated_users = 0
added_users = 0


def get_ou(ou):
	try:
		return adcontainer.ADContainer.from_dn(ou)
	except pywintypes.com_error:
		raise

def update_password(cn, password):
	user = aduser.ADUser.from_cn(cn)
	user.set_password(password)

def add_ad_user(ou, cn, single_attributes=None, multi_attributes=None):
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

def disable_user(cn):
	user = aduser.ADUser.from_cn(cn)
	user.disable()

def enable_user(cn):
	user = aduser.ADUser.from_cn(cn)
	user.enable()


def check_user_exists(cn):
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

def count_billable_cn():
	r = get_count_dn()
	billable_group = r['billable_group']
	l = adgroup.ADGroup(distinguished_name=billable_group).get_members(recursive=True)
	count=0
	for item in l:
		count +=1
	update_count(count)

@apiAuth
def get_count_dn():
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
def update_count(count):
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
def task_check():
	params = {'apikey': config.apikey, 'secret': config.private_key, 'org_id': config.org_id}
	return requests.get(config.host + 'api/tasks', params=params)

test = 0

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='MADST Client', prog='MADST-client')
	parser.add_argument('-d', '--dry-run', help='Shows you what actions would be taken', action='store_true')
	args = parser.parse_args()
if test:
	print("Running in test mode.")
while True:
	# for key, value in task_check().json().items():
	# 	if value['status']['id'] == 1:
	# 		if value['type'] == 'create':
	# 			cn = value['user']['first_name'] + ' ' + value['user']['last_name']
	# 			password = value['user']['sync_password']
	# 			password = decrypt(password.encode('utf-8'), config.private_key.encode('utf-8')).decode('utf-8')
	# 			if check_user_exists(cn) is True:
	# 				try:
	# 					update_password(cn, password)
	# 					print('Updated User {}'.format(cn))
	# 					change_task_status(value['id'], '3')
	# 					print("Task {} changed to status {}".format(value['id'], '3'))
	# 				except:
	# 					change_task_status(value['id'], '4')
	# 					print("Task {} changed to status {}".format(value['id'], '4'))
	# 			else:
	# 				# User doesn't exist, create them
	# 				try:
	# 					if not test:
	# 						try:
	# 							add_ad_user(get_ou(value['organization']['admin_ou']), cn, single_attributes=value['attributes']['single_attributes'], multi_attributes=value['attributes']['multi_attributes'])
	# 						except pyadexceptions.InvalidAttribute:
	# 							change_task_status(value['id'], '5')
	# 							print("Task {} changed to status {}".format(value['id'], '5'))
	# 							raise
	# 						update_password(cn, password)
	# 						print('Added User {}'.format(cn))
	# 						added_users = added_users + 1
	# 						change_task_status(value['id'], '3')
	# 						print("Task {} changed to status {}".format(value['id'], '3'))
	# 					elif test:
	# 						print("Would have added user {} to ou {} with {} single attributes, and {} multi attributes.".format(cn, value['organization']['admin_ou'], value['attributes']['single_attributes'], value['attributes']['multi_attributes']))
	# 						print("Would have changed task id {} to status {}".format(value['id'], '3'))
	# 				except:
	# 					if not value['id']['status']['id'] == 5:
	# 						change_task_status(value['id'], '4')
	# 						print("Task {} changed to status {}".format(value['id'], '4'))
	# 					print("Failed to add user {} in ou {}".format(cn, value['organization']['admin_ou']))
	# 					raise
	# 		if value['type'] == 'disable':
	# 			cn = value['user']['first_name'] + ' ' + value['user']['last_name']
	# 			try:
	# 				disable_user(cn)
	# 				change_task_status(value['id'], '3')
	# 				print("Task {} changed to status {}".format(value['id'], '3'))
	# 			except:
	# 				change_task_status(value['id'], '4')
	# 				print("Task {} changed to status {}".format(value['id'], '4'))
	# 		if value['type'] == 'enable':
	# 			cn = value['user']['first_name'] + ' ' + value['user']['last_name']
	# 			try:
	# 				enable_user(cn)
	# 				change_task_status(value['id'], '3')
	# 				print("Task {} changed to status {}".format(value['id'], '3'))
	# 			except:
	# 				change_task_status(value['id'], '4')
	# 				print("Task {} changed to status {}".format(value['id'], '4'))
	# 	else:
	# 		print('No new issues')
	count_billable_cn()
	# if added_users:
	# 	print("Added {} users".format(added_users))
	# if updated_users:
	# 	print("Updated {} users".format(updated_users))
	time.sleep(5)
