from django.conf.urls.defaults import *
from views import *
from . import get_viewer_urls

urlpatterns = patterns('',
                       *get_viewer_urls()
)
