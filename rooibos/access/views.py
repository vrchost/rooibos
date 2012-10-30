from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.views import login as dj_login, logout as dj_logout
from django.conf import settings
from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME
from models import AccessControl, update_membership_by_ip
from . import check_access, get_effective_permissions_and_restrictions, get_accesscontrols_for_object
from rooibos.statistics.models import Activity
import re


def login(request, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME,
          *args, **kwargs):
    if request.user.is_authenticated():
        # Similar redirect_to processing as in django.contrib.auth.views.login
        redirect_to = request.REQUEST.get(redirect_field_name, '')
        # Light security check -- make sure redirect_to isn't garbage.
        if not redirect_to or ' ' in redirect_to:
            redirect_to = settings.LOGIN_REDIRECT_URL
        # Heavier security check -- redirects to http://example.com should
        # not be allowed, but things like /view/?param=http://example.com
        # should be allowed. This regex checks if there is a '//' *before* a
        # question mark.
        elif '//' in redirect_to and re.match(r'[^\?]*//', redirect_to):
            redirect_to = settings.LOGIN_REDIRECT_URL
        return HttpResponseRedirect(redirect_to)
    try:
        response = dj_login(request, *args, **kwargs)
    except ValueError:
        # Certain values in the database password field can cause a ValueError
        # in that case, return a redirect back to the login page
        return HttpResponseRedirect((login_url or reverse('login')) + '?' + request.GET.urlencode())
    if type(response) == HttpResponseRedirect:
        # Successful login, add user to IP based groups
        update_membership_by_ip(request.user, request.META['REMOTE_ADDR'])
        Activity.objects.create(event='login',
                                request=request,
                                content_object=request.user)

    return response


def logout(request, *args, **kwargs):
    if request.session.get('unsafe_logout'):
        return render_to_response('unsafe_logout.html',
                                  {},
                                  context_instance=RequestContext(request))
    else:
        kwargs['next_page'] = request.GET.get('next', kwargs.get('next_page', settings.LOGOUT_URL))
        return dj_logout(request, *args, **kwargs)


def effective_permissions(request, app_label, model, id, name):
    try:
        contenttype = ContentType.objects.get(app_label=app_label, model=model)
        object = contenttype.get_object_for_this_type(id=id)
    except ObjectDoesNotExist:
        raise Http404
    check_access(request.user, object, manage=True, fail_if_denied=True)

    username = request.GET.get('user')
    if username:
        acluser = User.objects.filter(username=username)
        if acluser:
            acluser = acluser[0]
            acl = get_effective_permissions_and_restrictions(acluser, object, assume_authenticated=True)
        else:
            request.user.message_set.create(message="No user with username '%s' exists." % username)
            acl = None
    else:
        acluser = None
        acl = None

    return render_to_response('access_effective_permissions.html',
                              {'object': object,
                               'contenttype': contenttype,
                               'acluser': acluser,
                               'acl': acl,
                               'qsuser': username,
                               },
                              context_instance=RequestContext(request))


def modify_permissions(request, app_label, model, id, name):

    try:
        contenttype = ContentType.objects.get(app_label=app_label, model=model)
        object = contenttype.get_object_for_this_type(id=id)
    except ObjectDoesNotExist:
        raise Http404
    check_access(request.user, object, manage=True, fail_if_denied=True)

    permissions = get_accesscontrols_for_object(object)

    def tri_state(value):
        return None if value == 'None' else value == 'True'

    class ACForm(forms.Form):
        read = forms.TypedChoiceField(choices=((None, 'Not set'), (True, 'Allowed'), (False, 'Denied')), coerce=tri_state)
        write = forms.TypedChoiceField(choices=((None, 'Not set'), (True, 'Allowed'), (False, 'Denied')), coerce=tri_state)
        manage = forms.TypedChoiceField(choices=((None, 'Not set'), (True, 'Allowed'), (False, 'Denied')), coerce=tri_state)
        restrictions = forms.CharField(widget=forms.Textarea(attrs={'style': 'max-height: 100px;'}), required=False)

        def clean_restrictions(self):
            r = unicode(self.cleaned_data['restrictions'])
            if not r:
                return None
            try:
                return dict(map(unicode.strip, kv.split('=', 1)) for kv in filter(None, map(unicode.strip, r.splitlines())))
            except Exception, e:
                raise forms.ValidationError('Please enter one key=value per line')

    if request.method == "POST":
        acobjects = AccessControl.objects.filter(id__in=request.POST.getlist('ac'),
                                             content_type=contenttype,
                                             object_id=id)
        if request.POST.get('delete'):
            acobjects.delete()
            return HttpResponseRedirect(request.get_full_path())
        else:
            ac_form = ACForm(request.POST)
            if ac_form.is_valid():

                def set_ac(ac):
                    ac.read = ac_form.cleaned_data['read']
                    ac.write = ac_form.cleaned_data['write']
                    ac.manage = ac_form.cleaned_data['manage']
                    ac.restrictions = ac_form.cleaned_data['restrictions']
                    ac.save()

                map(set_ac, acobjects)

                username = request.POST.get('adduser')
                if username:
                    try:
                        user = User.objects.get(username=username)
                        ac = AccessControl.objects.filter(user=user, content_type=contenttype, object_id=id)
                        if ac:
                            set_ac(ac[0])
                        else:
                            set_ac(AccessControl(user=user, content_type=contenttype, object_id=id))
                    except User.DoesNotExist:
                        request.user.message_set.create(message="No user with username '%s' exists." % username)

                groupname = request.POST.get('addgroup')
                if groupname:
                    try:
                        group = Group.objects.get(name=groupname)
                        ac = AccessControl.objects.filter(usergroup=group, content_type=contenttype, object_id=id)
                        if ac:
                            set_ac(ac[0])
                        else:
                            set_ac(AccessControl(usergroup=group, content_type=contenttype, object_id=id))
                    except Group.DoesNotExist:
                        request.user.message_set.create(message="No group with name '%s' exists." % groupname)

                return HttpResponseRedirect(request.get_full_path())
    else:
        ac_form = ACForm()

    return render_to_response('access_modify_permissions.html',
                              {'object': object,
                               'contenttype': contenttype,
                               'permissions': permissions,
                               'ac_form': ac_form,
                               },
                              context_instance=RequestContext(request))
