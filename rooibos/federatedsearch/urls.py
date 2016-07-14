from django.conf.urls import patterns, url
from views import sidebar_api


urlpatterns = patterns(
    '',
    url(r'^api/sidebar/$', sidebar_api, name='federatedsearch-sidebar-api'),
)
