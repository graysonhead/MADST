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
    pass