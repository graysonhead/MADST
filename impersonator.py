import win32security
import win32con
import win32api
from win32file import error as Win32Exception
import sys

class Impersonate(object):
    def __init__(self, username, password, domain=''):
        self.username = username
        self.password = password
        self.domain = domain

    def logonUser(self):
        self.handle = win32security.LogonUser(self.username, self.domain, self.password,
                                              win32con.LOGON32_LOGON_INTERACTIVE, win32con.LOGON32_PROVIDER_DEFAULT)
        win32security.ImpersonateLoggedOnUser(self.handle)

    def logoffUser(self):
        win32security.RevertToSelf()
        self.handle.Close()

