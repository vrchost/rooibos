from django.conf.urls.defaults import patterns, url
from views import thumbnail, download

urlpatterns = patterns(
    '',
    url(
        r'^thumb/(?P<template>[^/]+)/$',
        thumbnail,
        name='pptexport-thumbnail'
    ),
    url(
        r'^download/(?P<id>\d+)/(?P<template>[^/]+)/$',
        download,
        name='pptexport-download'
    ),
)
