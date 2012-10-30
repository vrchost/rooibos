from django.contrib.auth import login as dj_login, authenticate as dj_authenticate, logout as dj_logout
from rooibos.access.models import update_membership_by_ip

def login(request, user):
    dj_login(request, user)
    update_membership_by_ip(request.user, request.META['REMOTE_ADDR'])

authenticate = dj_authenticate

logout = dj_logout
