# Copyright 2010 VPAC
#
# This file is part of django_shibboleth.
#
# django_shibboleth is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# django_shibboleth is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with django_shibboleth  If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.template import loader, RequestContext
from django.shortcuts import render
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.conf import settings

from django_shibboleth.utils import parse_attributes
from django_shibboleth.forms import BaseRegisterForm
from django_shibboleth.signals import shib_logon_done


def render_forbidden(*args, **kwargs):
    kwargs.pop('mimetype', None)
    kwargs.pop('content_type', None)
    return HttpResponseForbidden(loader.render_to_string(*args, **kwargs))


def shib_register(request, RegisterForm=BaseRegisterForm,
                  register_template_name='shibboleth/register.html'):

    attr, error = parse_attributes(request.META)


    next = None
    if request.method == "POST" and "next" in request.POST:
        next = request.POST["next"]
    elif request.method == "GET" and "next" in request.GET:
        next = request.GET["next"]

    if next is not None:
        was_redirected = True
        redirect_url = next
    else:
        was_redirected = False
        redirect_url = settings.LOGIN_REDIRECT_URL

    context = {'shib_attrs': attr,
               'was_redirected': was_redirected}
    if error:
        return render_forbidden('shibboleth/attribute_error.html',
                                  context,
                                  request=request)
    try:
        username = attr[settings.SHIB_USERNAME]
        # TODO this should log a misconfiguration.
    except:
        return render_forbidden('shibboleth/attribute_error.html',
                                  context,
                                  request=request)

    if not attr[settings.SHIB_USERNAME] or attr[settings.SHIB_USERNAME] == '':
        return render_forbidden('shibboleth/attribute_error.html',
                                  context,
                                  request=request)

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(attr)
    try:
        user = User.objects.get(username=attr[settings.SHIB_USERNAME])
    except User.DoesNotExist:
        form = RegisterForm()
        context = {'form': form,
                   'next': redirect_url,
                   'shib_attrs': attr,
                   'was_redirected': was_redirected}
        return render(request, register_template_name,
                                  context)

    user.set_unusable_password()
    try:
        user.first_name = attr[settings.SHIB_FIRST_NAME]
        user.last_name = attr[settings.SHIB_LAST_NAME]
        user.email = attr[settings.SHIB_EMAIL]
    except:
        pass
    user.save()

    user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, user)
    shib_logon_done.send(sender=shib_register, user=user, shib_attrs=attr)

    if not redirect_url or '//' in redirect_url or ' ' in redirect_url:
        redirect_url = settings.LOGIN_REDIRECT_URL

    return HttpResponseRedirect(redirect_url)


def shib_meta(request):

    meta_data = request.META.items()

    return render(request, 'shibboleth/meta.html',
                              {'meta_data': meta_data})
