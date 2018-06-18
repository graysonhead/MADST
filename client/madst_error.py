import sys

class madst_error(Exception):
    '''Base class '''
    def __init__(self, str):
        super().__init__(str)


class madst_config_error(madst_error):
    '''When something is wrong with the config.'''
    def __init__(self, str):
        super().__init__(str)