from . import services


class WorkersService(services.Service):

    _svc_name_ = "MDID Workers"
    _svc_display_name_ = "MDID Workers"
    _exe_args_ = "runworkers"
