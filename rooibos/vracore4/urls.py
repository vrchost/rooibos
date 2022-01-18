from django.conf.urls import url

from .views import record_as_json

urlpatterns = [
    url(r'^record/(?P<identifier>\d+)/?$', record_as_json, name='vracore4-record'),
]
