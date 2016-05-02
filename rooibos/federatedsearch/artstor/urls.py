from django.conf.urls.defaults import patterns, url
from views import search


urlpatterns = patterns(
    '',
    url(r'^artstor/$', search, name='artstor-search'),
)
