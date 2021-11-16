from django.utils.deprecation import MiddlewareMixin

PAGEHELP = 'HELP'


class PageHelp(MiddlewareMixin):

    def process_view(self, request, view_func, view_args, view_kwargs):
        if PAGEHELP in view_kwargs:
            request.pagehelp = view_kwargs[PAGEHELP]
            del view_kwargs[PAGEHELP]
