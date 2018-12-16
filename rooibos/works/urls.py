from django.conf.urls import url
from .views import search, metadata, works

urlpatterns = [
    url(r'^search/$', search),
    url(r'^metadata/(?P<record_id>\d+)/$', metadata),
    url(r'^works/$', works, name='works'),
]
