import hashlib,binascii
import hmac
from enum import Enum
import ssl
from ldap3 import Server, Connection, SIMPLE, KERBEROS, Tls, SASL, ALL, NTLM, SUBTREE
from errors import *
class Ldap_Server_Type(Enum):
     Windows_AD=1
     FreeIPA=2

class Ldap_Operations(object):
     #"single star" syntax ignores unspecified positional args
     # and provides keyword-only arguments, see PEP-3102
     def __init__(self, type, *, server=None, domain=None, user=None, ntlm_hash=None, plaintext_pw=None):
          if not server and user and domain:
               raise MCL_Error('Server, user, and domain are required for LDAP Operations')
          self.user=user
          self.domain=domain
          if type == Ldap_Server_Type.Windows_AD:
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
          elif type == Ldap_Server_Type.FreeIPA:
               # TODO: something that will actually work here.
               tls = ssl.create_default_context(
                    ssl.Purpose.CLIENT_AUTH)
               self.server=Server(
                    server,
                    get_info=ALL, 
                    tls=tls, 
                    use_ssl=True)
               self.conn=Connection(
                    self.server, 
                    authentication=SASL, 
                    sasl_mechanism='EXTERNAL')

          else:
               raise LdapServerTypeError(type)

          try:
               self.conn.bind()
          except:
               raise MCL_Error("Could not bind to LDAP server: " + str(self.conn.result))

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

     def users_in_group(self, baseDN, groupDN):
          ret=self.conn.search(
               search_base=baseDN,
               search_filter='(memberOf='+groupDN+')',
               search_scope=SUBTREE,
               attributes=['cn']
          )
          return self.conn.entries.__len__()

if __name__ == '__main__':
     t=Ldap_Operations(Ldap_Server_Type.Windows_AD, server='10.233.51.3', domain='rsitex', user='spencer', plaintext_pw='notreal')
     print(t.serverInfo())
     print(t.users_in_group('DC=RSITEX,DC=COM','CN=RSI Employees,OU=Groups,OU=RSI,DC=RSITEX,DC=COM'))
