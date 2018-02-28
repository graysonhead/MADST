'''
MADST Client LDAP Errors
'''
class MCL_Error(Exception):
    '''
    Base Class for MCL Exceptions
    '''
    pass

class LdapServerTypeError(MCL_Error):
    '''
    Unsupported Server Type
    '''
    def __init__(self, msg):
        raise MCL_Error('Unsupported Server Type:' + str(msg))