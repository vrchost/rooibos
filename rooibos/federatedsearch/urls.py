from django.urls import re_path as url
from .views import sidebar_api


urlpatterns = [
    url(r'^api/sidebar/$', sidebar_api, name='federatedsearch-sidebar-api'),
]
