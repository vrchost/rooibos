from django.http import HttpResponseRedirect
from functions import impersonate, endimpersonation


def start(request):
    next = request.GET.get('next', '/')
    username = request.REQUEST.get('username')
    if username:
        impersonate(request, username)
    return HttpResponseRedirect(next)


def stop(request):
    next = request.GET.get('next', '/')
    endimpersonation(request)
    return HttpResponseRedirect(next)
