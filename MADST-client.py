import requests
from Crypto.Cipher import AES
import base64
from pyad import adbase, adcomputer, adcontainer, adsearch, adquery, addomain, pyad, aduser, adgroup, pyadexceptions
import re

host = 'http://10.233.51.213:5000/'
org_id = 3
private_key = 'MAW9G6IHEQIANE2UD1YE4SCFIZGY6D3Y'

r = requests.get('http://10.233.51.213:5000/api/tasks/{}'.format(org_id))

def get_ou(ou):
	try:
		return adcontainer.ADContainer.from_dn(ou)
	except pywintypes.com_error:
		raise


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


def getOu(ou):
	try:
		return adcontainer.ADContainer.from_dn(ou)
	except pywintypes.com_error:
		print('Something went wrong connecting to AD. Ensure that you are running this script on a machine connected to AD with admin credentials.')
	else:
		pass

def decrypt(string, key):
	cipher = AES.new(key,AES.MODE_ECB)
	passout = cipher.decrypt(base64.b64decode(string))
	return passout.strip()

''' Lets do stuff '''
password = r.json()['0']['user']['sync_password']
password = decrypt(password, private_key).decode('utf-8')

for key, value in r.json().items():
	if value['status']['id'] == 1:
		cn = value['user']['first_name'] + ' ' + value['user']['last_name']
		if check_user_exists(cn):
			#update user
			print('User exists')
		else:
			# User doesn't exist, create them
			add_ad_user(get_ou(value['organization']['admin_ou']), cn)
			print('Added User')
	else:
		print('No new issues')