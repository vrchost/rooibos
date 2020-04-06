from django.conf.urls import url
from .views import manage, create, edit, duplicate, browse, password, \
    record_usage, manifest, transparent_png, missing_png


urlpatterns = [
    url(r'^manage/$', manage, name='presentation-manage'),
    url(r'^create/$', create, name='presentation-create'),
    url(
        r'^edit/(?P<id>\d+)/(?P<name>[-\w]+)/$',
        edit,
        name='presentation-edit'
    ),
    url(
        r'^duplicate/(?P<id>\d+)/(?P<name>[-\w]+)/$',
        duplicate,
        name='presentation-duplicate'
    ),
    url(r'^browse/$', browse, name='presentation-browse'),
    url(
        r'^password/(?P<id>\d+)/(?P<name>[-\w]+)/$',
        password,
        name='presentation-password'
    ),
    url(
        r'^record-usage/(?P<id>\d+)/(?P<name>[-\w]+)/$',
        record_usage,
        name='presentation-record-usage'
    ),
    url(
        r'^manifest/(?P<id>\d+)/(?P<name>[-\w]+)/$',
        manifest,
        name='presentation-manifest',
    ),
    url(
        r'^blank-slide/(?P<extra>.*)$',
        transparent_png,
        name='presentation-blank-slide'
    ),
    url(
        r'^missing-slide/(?P<extra>.*)$',
        missing_png,
        name='presentation-missing-slide'
    ),
]
