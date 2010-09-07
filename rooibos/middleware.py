import logging
from django.conf import settings

class Middleware:
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if view_kwargs.has_key('master_template'):
            request.master_template = view_kwargs['master_template']
            del view_kwargs['master_template']
        return None
    
    def process_request(self, request):
        # To support SWFUpload, copy the provided session key from POST into COOKIES
        # since Flash does not send browser cookies with its requests
        if (request.method == 'POST' and
            request.POST.get('swfupload') == 'true' and
            request.POST.has_key(settings.SESSION_COOKIE_NAME)):
            request.COOKIES[settings.SESSION_COOKIE_NAME] = request.POST[settings.SESSION_COOKIE_NAME]
    
    def process_response(self, request, response):
        # Remove the Vary header for content loaded into Flash, otherwise caching is broken
        if request.GET.get('flash') == '1':
            try:
                del response['Vary']
            except KeyError:
                pass
        return response