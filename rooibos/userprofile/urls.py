from django.conf.urls import patterns, url
from views import load_settings_view, store_settings_view

urlpatterns = patterns(
    '',
    url(r'^load/$', load_settings_view, name='userprofile-load'),
    url(r'^store/$', store_settings_view, name='userprofile-store'),
)
