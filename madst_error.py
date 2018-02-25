import sys

class madst_error(Exception):
    '''Base class '''
    def __init__(self, str):
        s = "madst_error." + str
        print(s)
        ##TODO: log handling (windows service & syslog)

class madst_config_error(madst_error):
    '''When something is wrong with the config.'''
    def __init__(self, str):
        s = "config: " + str
        madst_error.__init__(s)
        sys.exit()