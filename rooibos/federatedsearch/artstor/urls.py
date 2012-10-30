from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^artstor/$', search, name='artstor-search'),
)
