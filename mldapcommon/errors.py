'''
MADST Client LDAP Errors
'''


class ML_Error(Exception):
	'''
	Base Class for MCL Exceptions
	'''
	pass

class LdapServerTypeError(ML_Error):


	'''
	Unsupported Server Type
	'''


	def __init__(self, msg):
		super().__init__('Unsupported Server Type:' + str(msg))

class LdapBindError(ML_Error):
	'''
	Failed to bind
	'''


	def __init__(self, msg):
		super().__init__('Failed to bind account:' + str(msg))

class LdapConnectError(ML_Error):
	'''
	Failed to connect
	'''

	def __init__(self, msg):
		super().__init__('Failed to connect to server:' + str(msg))