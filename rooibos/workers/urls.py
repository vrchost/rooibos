from django.conf.urls import patterns, url
from views import joblist, download_attachment

urlpatterns = patterns(
    '',
    url(r'^jobs/$', joblist, name='workers-jobs'),
    url(r'^attachment/(?P<url>[-_a-z0-9]+\.txt)/$', download_attachment,
        name='workers-download-attachment'),
)
