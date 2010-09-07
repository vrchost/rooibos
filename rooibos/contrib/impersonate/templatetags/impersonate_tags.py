from django import template
from django.template.loader import render_to_string
from impersonate.functions import get_real_user, get_available_users

register = template.Library()


class ImpersonationFormNode(template.Node):
    def render(self, context):
        current = get_real_user(context['request'])
        users = get_available_users(current or context['request'].user.username)
        if users:
            return render_to_string('impersonation_form.html',
                                    {'users': users,
                                     'current': current,
                                     'request': context['request'],})
        else:
            return ''
    

@register.tag
def impersonation_form(parser, token):
    return ImpersonationFormNode()
