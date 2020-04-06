from django.conf.urls import url
from .views import download

urlpatterns = [
    url(
        r'^download/(?P<id>\d+)/$',
        download,
        name='pptexport-download'
    ),
]
