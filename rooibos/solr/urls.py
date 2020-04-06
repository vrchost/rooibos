from django.conf.urls import url
from .views import search, search_facets, search_json, browse, overview, \
    fieldvalue_autocomplete, search_form, terms

urlpatterns = [
    url(r'^explore/$', search, name='solr-search'),
    url(r'^explore/(?P<id>\d+)/(?P<name>[\w-]+)/$', search,
        name='solr-search-collection'),
    url(r'^explore-facets/$', search_facets, name='solr-search-facets'),
    url(r'^explore-facets/(?P<id>\d+)/(?P<name>[\w-]+)/$', search_facets,
        name='solr-search-collection-facets'),
    url(r'^api/search/$', search_json, name='api-solr-search'),
    url(r'^api/search/(?P<id>\d+)/(?P<name>[\w-]+)/$', search_json,
        name='api-solr-search-collection'),
    url(r'^selected/$', search, kwargs={'selected': True},
        name='solr-selected'),
    url(r'^selected-facets/$', search_facets, kwargs={'selected': True},
        name='solr-selected-facets'),
    url(r'^browse/$', browse, name='solr-browse'),
    url(r'^terms/$', terms, name='solr-terms'),
    url(r'^browse/(?P<id>\d+)/(?P<name>[\w-]+)/$', browse,
        name='solr-browse-collection'),
    url(r'^overview/$', overview, name='solr-overview'),
    url(r'^api/autocomplete/$', fieldvalue_autocomplete,
        name='api-solr-autocomplete'),
    url(r'^search/$', search_form, name='solr-searchform'),
]
