from django.conf.urls import url
from .views import effective_permissions, modify_permissions

urlpatterns = [
    url(
        r'^effective-permissions/(?P<app_label>[\w-]+)/(?P<model>[\w-]+)/'
        r'(?P<id>\d+)/(?P<name>[\w-]+)/$',
        effective_permissions,
        name='access-effective-permissions'
    ),
    url(
        r'^modify/(?P<app_label>[\w-]+)/(?P<model>[\w-]+)/'
        r'(?P<id>\d+)/(?P<name>[\w-]+)/$',
        modify_permissions,
        name='access-modify-permissions'
    ),
]
