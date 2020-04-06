from django.conf.urls import url
from .views import search


urlpatterns = [
    url(r'^artstor/$', search, name='artstor-search'),
]
