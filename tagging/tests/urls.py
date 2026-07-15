"""Test urls for tagging."""
from django.urls import re_path

from tagging.tests.models import Article
from tagging.views import TaggedObjectList


class StaticTaggedObjectList(TaggedObjectList):
    tag = 'static'
    queryset = Article.objects.all()


urlpatterns = [
    re_path(r'^static/$', StaticTaggedObjectList.as_view()),
    re_path(r'^static/related/$', StaticTaggedObjectList.as_view(
        related_tags=True)),
    re_path(r'^no-tag/$', TaggedObjectList.as_view(model=Article)),
    re_path(r'^no-query-no-model/$', TaggedObjectList.as_view()),
    re_path(r'^(?P<tag>[^/]+(?u))/$', TaggedObjectList.as_view(model=Article)),
]
