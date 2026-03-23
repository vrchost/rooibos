from django.urls import re_path as url
from .views import search, flickr_select_record

urlpatterns = [
    url(r'^search/', search, name='flickr-search'),
    url(r'^select/', flickr_select_record, name='flickr-select'),
]
