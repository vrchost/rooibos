from django.conf.urls import url
from .views import manage, create, edit, duplicate, browse, password, \
    record_usage, manifest, manifest_v3, manifest_from_search_v3, \
    annotation_list, transparent_png, missing_png


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
        r'^manifest-from-search/$',
        manifest_from_search_v3,
        name='presentation-from-search-manifest',
    ),
    url(
        r'^manifest-v3/(?P<id>\d+)/(?P<name>[-\w]+)/$',
        manifest_v3,
        name='presentation-manifest-v3',
    ),
    url(
        r'^annotation-list/(?P<id>\d+)/(?P<name>[-\w]+)/(?P<slide_id>\d+)/$',
        annotation_list,
        name='presentation-annotation-list',
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
