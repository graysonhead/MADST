from Cryptodome.Cipher import AES
import base64
from pyad import adbase, adcomputer, adcontainer, adsearch, adquery, addomain, pyad, aduser, adgroup, pyadexceptions
import time
import argparse
import ApiCalls
from madst_error import *
#from impersonator import *
from config import Config

config = Config()
def get_ou(ou):
	try:
		return adcontainer.ADContainer.from_dn(ou)
	except pywintypes.com_error:
		raise


def update_password(cn, password):
	user = aduser.ADUser.from_cn(cn)
	user.set_password(password)


def create_ad_user(ou, cn):
	ou.create_user(cn)


def update_user_attributes(cn, single_attributes=None, multi_attributes=None):
	''' Creates a new user in the designated OU '''
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


def count_billable_cn():
	r = ApiCalls.get_count_dn()
	group = adgroup.ADGroup.from_dn(r['billable_group'])
	count = group.get_members().__len__()

	ApiCalls.update_count(count)
	return count


def main():
	for key, value in ApiCalls.task_check().items():
		if value['status']['id'] == 1:
			if value['type'] == 'create':
				cn = value['user']['first_name'] + ' ' + value['user']['last_name']
				ou = get_ou(value['organization']['admin_ou'])
				password = value['user']['sync_password']
				password = decrypt(password.encode('utf-8'), Config.private_key.encode('utf-8')).decode('utf-8')
				if check_user_exists(cn) is True:
					try:
						update_user_attributes(
							cn,
							single_attributes=value['attributes']['single_attributes'],
							multi_attributes=value['attributes']['multi_attributes']
						)
						update_password(cn, password)
						print('Updated User {}'.format(cn))
						ApiCalls.change_task_status(value['id'], '3')
						print("Task {} changed to status {}".format(value['id'], '3'))
					except:
						ApiCalls.change_task_status(value['id'], '4')
						print("Task {} changed to status {}".format(value['id'], '4'))
				else:
					# User doesn't exist, create them
					try:
#						if not test:
						try:
							create_ad_user(ou, cn)
							update_user_attributes(
								cn,
								single_attributes=value['attributes']['single_attributes'],
								multi_attributes=value['attributes']['multi_attributes']
							)
						except pyadexceptions.InvalidAttribute:
							ApiCalls.change_task_status(value['id'], '5')
							print("Task {} changed to status {}".format(value['id'], '5'))
							raise
						update_password(cn, password)
						print('Added User {}'.format(cn))
						ApiCalls.change_task_status(value['id'], '3')
						print("Task {} changed to status {}".format(value['id'], '3'))
#						elif test:
#							print(
#								"Would have added user {} to ou {} with {} single attributes, and {} multi attributes.".format(
#									cn, value['organization']['admin_ou'], value['attributes']['single_attributes'],
#									value['attributes']['multi_attributes']))
#							print("Would have changed task id {} to status {}".format(value['id'], '3'))
					except:
						if not value['status']['id'] == 5:
							ApiCalls.change_task_status(value['id'], '4')
							print("Task {} changed to status {}".format(value['id'], '4'))
						print("Failed to add user {} in ou {}".format(cn, value['organization']['admin_ou']))
						raise
			if value['type'] == 'disable':
				cn = value['user']['first_name'] + ' ' + value['user']['last_name']
				try:
					disable_user(cn)
					ApiCalls.change_task_status(value['id'], '3')
					print("Task {} changed to status {}".format(value['id'], '3'))
				except:
					ApiCalls.change_task_status(value['id'], '4')
					print("Task {} changed to status {}".format(value['id'], '4'))
			if value['type'] == 'enable':
				cn = value['user']['first_name'] + ' ' + value['user']['last_name']
				try:
					enable_user(cn)
					ApiCalls.change_task_status(value['id'], '3')
					print("Task {} changed to status {}".format(value['id'], '3'))
				except:
					ApiCalls.change_task_status(value['id'], '4')
					print("Task {} changed to status {}".format(value['id'], '4'))
	count_billable_cn()


if __name__ == '__main__':
	updated_users = 0

	parser = argparse.ArgumentParser(description='MADST Client', prog='MADST-client')
	parser.add_argument('-d', '--dry-run', help='Shows you what actions would be taken', action='store_true')
	parser.add_argument('--test', help='enables test functionality', action='store_true')
	pargs = parser.parse_args()
	if pargs.test:
		print("Running in test mode.")
	test = pargs.test
	dry_run = pargs.dry_run

	try:
		while True:
			main()
			time.sleep(5)
	except Exception as e:
		raise
	sys.exit()
