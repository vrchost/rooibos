
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.cache import cache_control
from django.db.models import Q
from .functions import impersonate, endimpersonation, get_available_users, get_real_user


def start(request):
    next = request.GET.get('next', '/')
    username = request.POST.get('username')
    if username:
        current = get_real_user(request)
        available_user = get_available_users(current or request.user.username).filter(username=username)
        if available_user.count() == 1:
            impersonate(request, username)
    return HttpResponseRedirect(next)


def stop(request):
    next = request.GET.get('next', '/')
    endimpersonation(request)
    return HttpResponseRedirect(next)


@cache_control(no_cache=True)
def autocomplete_user(request):
    query = request.GET.get('q', '').lower()
    try:
        limit = max(10, min(25, int(request.GET.get('limit', '10'))))
    except ValueError:
        limit = 10
    if not query or not request.user.is_authenticated():
        return HttpResponse(content='')

    current = get_real_user(request)
    available_users = get_available_users(current or request.user.username)
    users = list(available_users.filter(username__istartswith=query).values_list('username', flat=True)[:limit])
    if len(users) < limit:
        users.extend(available_users.filter(~Q(username__istartswith=query), username__icontains=query)
                     .values_list('username', flat=True)[:limit - len(users)])
    return HttpResponse(content='\n'.join(users))
