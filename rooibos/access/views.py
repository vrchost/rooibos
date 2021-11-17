from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.views import LoginView, LogoutView
from django import forms
from .models import AccessControl
from .functions import check_access, \
    get_effective_permissions_and_restrictions, get_accesscontrols_for_object
from rooibos.statistics.models import Activity
import logging

logger = logging.getLogger(__name__)


class LocalLoginView(LoginView):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.session.modified = True
            redirect_to = self.get_success_url()
            return HttpResponseRedirect(redirect_to)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        Activity.objects.create(
            event='login',
            request=self.request,
            content_type=ContentType.objects.get_for_model(User),
            object_id=self.request.user.id,
        )
        return super().form_valid(form)


class LocalLogoutView(LogoutView):

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.session.get('unsafe_logout'):
            return render(request, 'unsafe_logout.html')
        return response


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
            acl = get_effective_permissions_and_restrictions(
                acluser, object, assume_authenticated=True)
        else:
            messages.add_message(
                request,
                messages.INFO,
                message="No user with username '%s' exists." % username
            )
            acl = None
    else:
        acluser = None
        acl = None

    return render(
        request, 'access_effective_permissions.html',
        {
            'object': object,
            'contenttype': contenttype,
            'acluser': acluser,
            'acl': acl,
            'qsuser': username,
        }
    )


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
        read = forms.TypedChoiceField(
            choices=((None, 'Not set'), (True, 'Allowed'), (False, 'Denied')),
            required=False,
            empty_value=None,
            coerce=tri_state
        )
        write = forms.TypedChoiceField(
            choices=((None, 'Not set'), (True, 'Allowed'), (False, 'Denied')),
            required=False,
            empty_value=None,
            coerce=tri_state
        )
        manage = forms.TypedChoiceField(
            choices=((None, 'Not set'), (True, 'Allowed'), (False, 'Denied')),
            required=False,
            empty_value=None,
            coerce=tri_state
        )
        restrictions = forms.CharField(
            widget=forms.Textarea(attrs={'style': 'max-height: 100px;'}),
            required=False
        )

        def clean_restrictions(self):
            r = str(self.cleaned_data['restrictions'])
            if not r:
                return None
            try:
                return dict(
                    list(map(str.strip, kv.split('=', 1)))
                    for kv in [
                        _f for _f in map(str.strip, r.splitlines()) if _f
                    ]
                )
            except Exception:
                raise forms.ValidationError(
                    'Please enter one key=value per line')

    if request.method == "POST":
        acobjects = AccessControl.objects.filter(
            id__in=request.POST.getlist('ac'),
            content_type=contenttype,
            object_id=id
        )
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

                for acobject in acobjects:
                    set_ac(acobject)

                username = request.POST.get('adduser')
                if username:
                    try:
                        user = User.objects.get(username=username)
                        ac = AccessControl.objects.filter(
                            user=user, content_type=contenttype, object_id=id)
                        if ac:
                            set_ac(ac[0])
                        else:
                            set_ac(AccessControl(
                                user=user,
                                content_type=contenttype,
                                object_id=id
                            ))
                    except User.DoesNotExist:
                        messages.add_message(
                            request,
                            messages.INFO,
                            message="No user with username '%s' exists." %
                                    username
                        )

                groupname = request.POST.get('addgroup')
                if groupname:
                    try:
                        group = Group.objects.get(name=groupname)
                        ac = AccessControl.objects.filter(
                            usergroup=group,
                            content_type=contenttype,
                            object_id=id
                        )
                        if ac:
                            set_ac(ac[0])
                        else:
                            set_ac(AccessControl(
                                usergroup=group,
                                content_type=contenttype,
                                object_id=id
                            ))
                    except Group.DoesNotExist:
                        messages.add_message(
                            request,
                            messages.INFO,
                            message="No group with name '%s' exists." %
                                    groupname
                        )

                return HttpResponseRedirect(request.get_full_path())
    else:
        ac_form = ACForm()

    return render(
        request, 'access_modify_permissions.html',
        {
            'object': object,
            'contenttype': contenttype,
            'permissions': permissions,
            'ac_form': ac_form,
        }
    )
