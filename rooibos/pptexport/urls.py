from django.conf.urls import url
from views import thumbnail, download

urlpatterns = [
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
]
