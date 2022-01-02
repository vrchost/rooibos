from django.conf.urls import url

from .views import record

urlpatterns = [
    url(r'^record/(?P<id>\d+)/?$', record, name='vracore4-record'),
]
