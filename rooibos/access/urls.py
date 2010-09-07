from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^effective-permissions/(?P<app_label>[\w-]+)/(?P<model>[\w-]+)/(?P<id>\d+)/(?P<name>[\w-]+)/$', effective_permissions, name='access-effective-permissions'),
    url(r'^modify/(?P<app_label>[\w-]+)/(?P<model>[\w-]+)/(?P<id>\d+)/(?P<name>[\w-]+)/$', modify_permissions, name='access-modify-permissions'),
)
