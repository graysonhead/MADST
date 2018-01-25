import requests
from Cryptodome.Cipher import AES
import base64
from pyad import adbase, adcomputer, adcontainer, adsearch, adquery, addomain, pyad, aduser, adgroup, pyadexceptions
import re
import time
import argparse


host = 'http://10.233.51.213:5000/'
org_id = 3
private_key = 'MAW9G6IHEQIANE2UD1YE4SCFIZGY6D3Y'
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

def add_ad_user(ou, cn, attributes=False):
	''' Creates a new user in the designated OU '''
	ou.create_user(cn)
	user = aduser.ADUser.from_cn(cn)
	# user.update_attributes(attributes['singleVarAttrib'])
	# for key, value in attributes['multiVarAttrib'].items():
	# 	user.append_to_attribute(key, value)


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

def change_task_status(task_id, status_id):
	requests.put(host + 'api/task/' + str(task_id), data={'status': status_id})


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='MADST Client', prog='MADST-client')
	parser.add_argument('-d', '--dry-run', help='Shows you what actions would be taken', action='store_true')
	args = parser.parse_args()
while True:
	try:
		r = requests.get(host + 'api/tasks/{}'.format(org_id))
	except requests.exceptions.ConnectionError:
		print("A connection error occured, check the host and port and try again.")
	for key, value in r.json().items():
		if value['status']['id'] == 1:
			cn = value['user']['first_name'] + ' ' + value['user']['last_name']
			password = value['user']['sync_password']
			password = decrypt(password, private_key).decode('utf-8')

			if check_user_exists(cn):
				try:
					update_password(cn, password)
					print('Updated User {}'.format(cn))
					updated_users = updated_users + 1
					change_task_status(value['id'], '3')
					print("Task {} changed to status {}".format(value['id'], '3'))
				except:
					change_task_status(value['id'], '4')
					print("Task {} changed to status {}".format(value['id'], '4'))


			else:
				# User doesn't exist, create them
				try:
					add_ad_user(get_ou(value['organization']['admin_ou']), cn)
					print('Added User {}'.format(cn))
					added_users = added_users + 1
					change_task_status(value['id'], '3')
					print("Task {} changed to status {}".format(value['id'], '3'))
				except:
					change_task_status(value['id'], '4')
					print("Task {} changed to status {}".format(value['id'], '4'))
		else:
			print('No new issues')

	# if added_users:
	# 	print("Added {} users".format(added_users))
	# if updated_users:
	# 	print("Updated {} users".format(updated_users))
	time.sleep(5)
