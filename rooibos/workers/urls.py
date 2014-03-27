from django.conf.urls.defaults import patterns, url
from views import joblist

urlpatterns = patterns(
    '',
    url(r'^jobs/$', joblist, name='workers-jobs'),
)
