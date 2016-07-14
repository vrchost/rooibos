from django.conf.urls import patterns, url
from django.conf import settings

from views import start, stop, autocomplete_user

urlpatterns = patterns('',
    url(r'^start/', start, name='impersonation-start'),
    url(r'^stop/', stop, name='impersonation-stop'),
    url(r'^autocomplete/$', autocomplete_user, name='impersonation-autocomplete-user'),
)
