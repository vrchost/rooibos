from django.conf.urls.defaults import *

from views import search

urlpatterns = patterns('',
    url(r'^shared/$', search, name='shared-search'),
)
