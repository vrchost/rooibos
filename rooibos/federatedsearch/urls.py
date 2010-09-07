from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^api/sidebar/$', sidebar_api, name='federatedsearch-sidebar-api'),
)