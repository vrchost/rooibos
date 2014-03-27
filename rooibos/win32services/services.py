import os
import sys
import win32serviceutil
import win32service
import win32event
import win32api
import servicemanager

install_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
if not install_dir in sys.path: sys.path.append(install_dir)

from rooibos import settings


class Service(win32serviceutil.ServiceFramework):

    """
    Need to subclass this and set the following class variables:

    _svc_name_ = "SampleServer"
    _svc_display_name_ = "MDID Simple Sample Server"
    _exe_args_ = "runsimpleserver"
    """

    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, *args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def log(self, msg):
        servicemanager.LogInfoMsg(str(msg))

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            from django.core.management import execute_manager
            execute_manager(settings)
            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
        except Exception, ex:
            self.log('Exception: %s' % ex)
            self.SvcStop()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    @classmethod
    def get_class_string(cls):
        return '%s.%s' % (os.path.splitext(os.path.abspath(sys.modules[cls.__module__].__file__))[0], cls.__name__)
