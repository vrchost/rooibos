from django.conf.urls.defaults import patterns, url
from views import install


urlpatterns = patterns(
    '',
    url(r'^install/$', install, name='mediaviewer-install'),
)
