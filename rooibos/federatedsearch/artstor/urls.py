from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^photo-search/$', photo_search, name='artstor-photo-search'),
)