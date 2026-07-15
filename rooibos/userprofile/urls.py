from django.urls import re_path as url
from .views import load_settings_view, store_settings_view

urlpatterns = [
    url(r'^load/$', load_settings_view, name='userprofile-load'),
    url(r'^store/$', store_settings_view, name='userprofile-store'),
]
