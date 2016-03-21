from django.conf.urls.defaults import patterns, url
from .views import search, metadata, works

urlpatterns = patterns(
    '',
    url(r'^search/$', search),
    url(r'^metadata/(?P<record_id>\d+)/$', metadata),
    url(r'^works/$', works),
)
