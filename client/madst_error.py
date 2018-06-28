import sys

class MadstError(Exception):
    '''Base class '''
    def __init__(self, str):
        super().__init__(str)


class MadstConfigError(MadstError):
    '''When something is wrong with the config.'''
    def __init__(self, str):
        super().__init__(str)