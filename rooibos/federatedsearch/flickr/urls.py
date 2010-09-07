from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', main, name='flickr-main'),
    url(r'^authorize/$', authorize, name='flickr-authorize'),
    url(r'^people(/(?P<username>[\w-]+))?/$', people, name='flickr-people'),
    url(r'^photosets(/(?P<id>[\w@]+))?/$', photosets, name='flickr-photosets'),
    url(r'^set(/(?P<setid>\d+))?/$', flickrSet, name='flickr-set'),
    url(r'^import-set/$', import_set_photos, name='flickr-import-set'),
    url(r'^export-photo-frob/$', export_photo_get_frob, name='flickr-export-photo-frob'),
    url(r'^export-photo-upload/$', export_photo_upload, name='flickr-export-photo-upload'),
    url(r'^export-photo-list/$', export_photo_list, name='flickr-export-photo-list'),
    url(r'^photo-search/$', photo_search, name='flickr-photo-search'),
    url(r'^private-photo-search/$', private_photo_search, name='flickr-private-photo-search'),
    url(r'^select-flickr/$', select_flickr, name='flickr-select-flickr'),
    url(r'^import-photos/$', import_photos, name='flickr-import-photos'),
)