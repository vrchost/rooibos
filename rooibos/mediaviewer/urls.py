from django.conf.urls import url
from .views import install


urlpatterns = [
    url(r'^install/$', install, name='mediaviewer-install'),
]
