''' Importing Modules '''
import sys
import sys
import argparse
import csv
import re
from win32 import *
from pyad import *
import secrets
''' pyinstaller has trouble finding these modules, so they have been manually specified '''
from pyad import adbase
from pyad import adcomputer
from pyad import adcontainer
from pyad import adsearch
from pyad import adquery
from pyad import addomain
from pyad import pyad
''' Function Junction '''
def getOu(ou):
	try:
		return adcontainer.ADContainer.from_dn(ou)
	except pywintypes.com_error:
		print('Something went wrong connecting to AD. Ensure that you are running this script on a machine connected to AD with admin credentials.')
	else:
		pass
def detUserName(first, last):
		''' Generate a standardized username based on namingScheme variable '''
		if args.namingScheme == 'FirstL':
			userName = first + last[0]
		elif args.namingScheme == 'FLast':
			userName = first[0] + last
		return userName
def atribRegex(string):
	''' Perform string replacement on Attribute values '''
	string = re.sub(r"%userName%", userName, string)
	string = re.sub(r"%firstName%", args.firstName, string)
	return re.sub(r"%lastName%", args.lastName, string)
def createUserNameAtrib(first, last):
	''' Creates User Dict for account creation '''
	userDef = {'cn': first + ' ' + last,
		'displayName': first + ' ' + last,
		'name': first + ' ' + last,
		'sn': last}
	return userDef
def readFile(filename):
	''' Opens file and returns it's content '''
	with open (filename, 'rt') as in_file:
		contents = in_file.read()
		in_file.close()
	return contents
def parseAttributes(content):
	''' Parses Attribute file into dict '''
	singleVarAttributes = re.findall("single:.*", content)
	multiVarAttributes = re.findall("multi:.*", content)
	groupMembership = re.findall("group:.*", content)
	singleVarAttribDict = {}
	multiVarAttribDict = {}
	groups = []
	for n in range(len(singleVarAttributes)):
		singleVarAttributes[n] = singleVarAttributes[n].split(':', 1)[-1]
		singleVarAttributes[n] = atribRegex(singleVarAttributes[n])
		(key, val) = singleVarAttributes[n].split('=', 1)
		singleVarAttribDict[key] = val
	for n in range(len(groupMembership)):
		groupMembership[n] = groupMembership[n].split('=', 1)[-1]
		groups.append(groupMembership[n])
	for n in range(len(multiVarAttributes)):
		multiVarAttributes[n] = multiVarAttributes[n].split(':', 1)[-1]
		multiVarAttributes[n] = atribRegex(multiVarAttributes[n])
		(key, val) = multiVarAttributes[n].split('=', 1)
		if key in multiVarAttribDict:
			multiVarAttribDict[key].append(val)
		else:
			multiVarAttribDict[key] = [val]
	singleVarAttribDict.update(createUserNameAtrib(args.firstName, args.lastName))
	return {'singleVarAttrib': singleVarAttribDict, 'multiVarAttrib': multiVarAttribDict, 'groups': groups}
	
def checkUserExists(cn):
	''' Exit on error if you are trying to create an existing CN '''
	user = False
	try:
		user = aduser.ADUser.from_cn(cn)
	except:
		pass
	if user:
		print("A user with the CN \"" + cn + "\" was found in LDAP. Please make sure the user you are trying to create doesn't already exist.")
		sys.exit(2)
	else:
		pass
def addAdUser(ou, cn, attributes):
	''' Creates a new user in the designated OU '''
	ou.create_user(cn)
	user = aduser.ADUser.from_cn(userCn)
	user.update_attributes(attributes['singleVarAttrib'])
	for key, value in attributes['multiVarAttrib'].items():
		user.append_to_attribute(key, value)
def joinGroups(userCn, groups):
	''' Joins user to groups specified in attribute file '''
	user = aduser.ADUser.from_cn(userCn)
	for g in groups:
		group = adgroup.ADGroup.from_dn(g)
		group.add_members(user)
def gen_password(length=8, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"):
	''' Uses secrets library to generate random password '''
	return "".join([secrets.choice(charset) for _ in range(0, length)])
def setTempPasswd(cn, passLength):
	''' Changes user's password to randomly generated one, and then sets force_pwd_change '''
	passWord = gen_password(length=passLength)
	user = aduser.ADUser.from_cn(cn)
	user.set_password(passWord)
	user.force_pwd_change_on_login()
	return passWord
''' Arguments '''
if __name__ == '__main__':
	''' This section handles commandline arguments '''
	parser = argparse.ArgumentParser(description='Tool to add users to Active Directory')
	parser.add_argument('-c', '--create', help='Mode: Creates a new user', action='store_true')
	parser.add_argument('-r', '--reset-password', help='Mode: Resets a user\'s password', action='store_true')
	parser.add_argument('-f', '--first-name', dest='firstName', required=True, help='Define first name for new user creation')
	parser.add_argument('-l', '--last-name', dest='lastName', required=True, help='Define last name for new user creation')
	parser.add_argument('-O', '--ou-distinguished-name', required=True, dest='ouDestinguishedName', help='Define the parent OU for user creation')
	parser.add_argument('-A', '--attribute-file', required=True, dest='attributeFile', help='Text file containing LDAP attributes and values seperated by a space (one attribute per line)')
	parser.add_argument('-s', '--naming-scheme', default='FirstL', dest='namingScheme', choices=['FirstL', 'FLast'], help='Pick the username naming scheme for the user. FLast = ghead, firstl = graysonh. Default is FirstL')
	parser.add_argument('-y', dest='noPrompts', help='Supresses user confirmation prompts.', action='store_true')
	parser.add_argument('-p', '--password-length', type=int, default=8, dest='passLength', help='Set the charachter length of the generated password')
	args = parser.parse_args()
if args.create:
	userCn = args.firstName + ' ' + args.lastName
	userName = detUserName(args.firstName, args.lastName)
	userDef = {}
	try:
		userDef.update(parseAttributes(readFile(args.attributeFile)))
	except FileNotFoundError:
		print("The attribute file you specified was not found, please check the file name and try again.")
	else:
		pass
	ou = getOu(args.ouDestinguishedName)
	checkUserExists(userCn)
	if args.noPrompts:
		pass
	else:
		print("You will be creating a user with the following attributes: \n ===================")
		print(userDef)
		print("This will be added into the OU:\n =================")
		print(ou)
		userContinue = input("Would you like to enter this user into LDAP? (y/N):")
		if (userContinue == 'y' or userContinue == 'Y' or userContinue == 'Yes' or userContinue == 'yes'):
			pass
		else:
			sys.exit(0)
	addAdUser(ou, userCn, userDef)
	joinGroups(userCn, userDef['groups'])
	userPasswd = setTempPasswd(userCn, args.passLength)
	print(args.firstName + ' ' + args.lastName + '\'s password has been reset to: ' + userPasswd)

elif args.reset_password:
	userCn = args.firstName + ' ' + args.lastName
	userPasswd = setTempPasswd(userCn, args.passLength)
	print(args.firstName + ' ' + args.lastName + '\'s password has been reset to: ' + userPasswd)
	
	