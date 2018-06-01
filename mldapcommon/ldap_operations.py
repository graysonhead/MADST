import hashlib
from enum import IntEnum
import ssl
from ldap3 import Server, Connection, Tls, SASL, ALL, NTLM, SUBTREE, ALL_ATTRIBUTES
from mldapcommon.errors import *
from functools import wraps

class LdapServerType(IntEnum):
	Windows_AD=1
	FreeIPA=2
	Generic_LDAP=3


class LdapOperations(object):
	#"single star" syntax ignores unspecified positional args
	# and provides keyword-only arguments, see PEP-3102
	def __init__(self, type, *, server=None, domain=None, user=None, ntlm_hash=None, plaintext_pw=None, use_ssl=True, windows_user_format=False):
		if not server and user and domain:
			raise ML_Error('Server, user, and domain are required for LDAP Operations')
		self.user=user
		self.domain=domain
		if type == LdapServerType.Windows_AD:
			if ntlm_hash:
					self.ntlm_hash=ntlm_hash
			elif plaintext_pw:
					self.hash=self.ntlm_hash(plaintext_pw)
			else:
				raise ValueError('Windows AD requires ntlm_hash or plaintext_pw keyword.')

			self.server=Server(
					server,
					get_info=ALL)
			self.conn=Connection(
					self.server,
					user=self.domain + '\\' + self.user,
					password=self.hash,
					authentication=NTLM
			)
		elif type == LdapServerType.FreeIPA:
			# TODO: something that will actually work here.
			tls = ssl.create_default_context(
					ssl.Purpose.CLIENT_AUTH)
			self.server=Server(
					server,
					get_info=ALL,
					tls=tls,
					use_ssl=use_ssl)
			self.conn=Connection(
					self.server,
					authentication=SASL,
					sasl_mechanism='EXTERNAL')

		elif type == LdapServerType.Generic_LDAP:
			self.server=Server(
				server,
				get_info=ALL,
			)
			self.conn=Connection(
				self.server,
				user=user,
				password=plaintext_pw
			)

		else:
			raise LdapServerTypeError(type)

		'''
		Ldap3 doesn't raise exceptions on connection errors, so we make sure everything worked below
		'''
		if self.server.check_availability():
			pass
		else:
			raise LdapConnectError("Failed to connect to server")
		if self.conn.bind():
			pass
		else:
			raise LdapBindError("Incorrect Login information")

	def serverInfo(self):
		return self.server.info

	def ntlm_hash(self,pw):
		#correct function for ntlm hash
		h = hashlib.new(
			'md4',
			pw.encode('utf-16le')
		).hexdigest()

		## For some reason, this is the desired format (LM:NTLM):
		return '00000000000000000000000000000000:' + h

	def users_in_group(self, baseDN, groupDN, attributes=['cn']):
		self.conn.search(
			search_base=baseDN,
			search_filter='(memberOf='+groupDN+')',
			search_scope=SUBTREE,
			attributes=attributes
		)
		return self.conn.entries

	def find_dn_from_username(self, basedn, username, attributes=['userPrincipalName', 'user']):
		search_string = '(|'
		for a in attributes:
			search_string = search_string + '({}={})'.format(a, username)
		search_string = search_string + ')'
		self.conn.search(basedn, search_string, attributes='distinguishedName')
		try:
			return self.conn.entries[0].distinguishedName.value
		except IndexError:
			return None

if __name__ == '__main__':
	t=LdapOperations(
		LdapServerType.Windows_AD,
		server='10.233.51.3',
		domain='rsitex',
		user='spencer',
		plaintext_pw=''
	)
	print(t.serverInfo())
	print(t.users_in_group('DC=RSITEX,DC=COM','CN=RSI Employees,OU=Groups,OU=RSI,DC=RSITEX,DC=COM'))
