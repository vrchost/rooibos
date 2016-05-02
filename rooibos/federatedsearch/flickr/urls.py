from django.conf.urls.defaults import patterns, url
from views import search, flickr_select_record

urlpatterns = patterns(
    '',
    url(r'^search/', search, name='flickr-search'),
    url(r'^select/', flickr_select_record, name='flickr-select'),
)
