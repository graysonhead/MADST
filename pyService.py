import servicemanager
import traceback
import socket
import sys
import win32event
import win32service
import win32serviceutil
#change this import to the script you want
import MADST_Client as script

class pyService(win32serviceutil.ServiceFramework):
#set the names you want to show up in windows services manager
    _svc_name_ = "MADST Client Service"
    _svc_display_name_ = "MADST Client Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        rc = None
        while rc != win32event.WAIT_OBJECT_0:
            try:
                script.main()
            except:
                servicemanager.LogErrorMessage(traceback.format_exec())
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(pyService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(pyService)
