from django.conf.urls.defaults import patterns, url

from views import search, proxy_image, select, manage, edit

urlpatterns = patterns('',
    url(r'^search/$', search, name='shared-search'),
    url(r'^image/$', proxy_image, name='shared-proxy-image'),
    url(r'^select/$', select, name='shared-select'),
    url(r'^manage/$', manage, name='shared-manage'),
    url(r'^new/$', edit, name='shared-new'),
    url(r'^(?P<id>\d+)/(?P<name>[-\w]+)/edit/$', edit, name='shared-edit'),
)
