import sys
import ApiCalls

class MadstError(Exception):
    '''Base class '''
    def __init__(self, str):
        super().__init__(str)


class MadstConfigError(MadstError):
    '''When something is wrong with the config.'''
    def __init__(self, str):
        super().__init__(str)


class TaskFailed(MadstError):
    '''Change task status and log failed task.'''
    def __init__(self, str, taskinfo=None, taskid=None):
        ApiCalls.change_task_status(taskid, ApiCalls.TaskStatus.FAILED)
        if taskinfo is not None:
            str = '{}\n\n{}\n{}'.format(str, 'This error was raised for the following task:', taskinfo)
        super().__init__(str)