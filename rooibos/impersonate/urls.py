
from django.conf.urls import url
from .views import start, stop, autocomplete_user

urlpatterns = [
    url(r'^start/', start, name='impersonation-start'),
    url(r'^stop/', stop, name='impersonation-stop'),
    url(r'^autocomplete/$', autocomplete_user, name='impersonation-autocomplete-user'),
]
