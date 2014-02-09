from django.conf.urls.defaults import patterns, url

from views import search, proxy_image, select

urlpatterns = patterns('',
    url(r'^search/$', search, name='shared-search'),
    url(r'^image/$', proxy_image, name='shared-proxy-image'),
    url(r'^select/$', select, name='shared-select'),
)
