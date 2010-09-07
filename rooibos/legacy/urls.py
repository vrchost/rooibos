from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.conf import settings
from views import *
from rooibos.storage.views import retrieve

urlpatterns = patterns('',
    (r'^WebServices/ImageViewer.asmx/GetInfo$', direct_to_template,
        {'template': 'imageviewer_getinfo.xml',
         'extra_context': {'namespace': settings.WEBSERVICE_NAMESPACE, 'securelogin': settings.SECURE_LOGIN},
         'mimetype': 'text/xml'}),
    (r'^WebServices/ImageViewer.asmx/Login$', imageviewer_login, {}),
    (r'^WebServices/ImageViewer.asmx/GetSlideshow$', imageviewer_getslideshow, {}),
)
