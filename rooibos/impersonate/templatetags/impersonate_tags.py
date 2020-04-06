
from django import template
from django.template.loader import render_to_string
from django.template import RequestContext
from ..functions import get_real_user, get_available_users, can_impersonate_others

register = template.Library()


class ImpersonationFormNode(template.Node):
    def render(self, context):
        request = context['request']
        current = get_real_user(request)
        user_count = get_available_users(current or request.user.username).count()
        if user_count:
            if user_count <= 100:
                users = get_available_users(current or request.user.username).values_list('username', flat=True)
            else:
                users = None
            return render_to_string('impersonation_form.html',
                                    {'users': users,
                                     'current': current,
                                     'request': request,},
                                    request=request)
        else:
            return ''


@register.tag
def impersonation_form(parser, token):
    return ImpersonationFormNode()



@register.filter(name='can_realuser_impersonate_others')
def can_realuser_impersonate_others_filter(request):
    return can_impersonate_others(get_real_user(request) or request.user)
