from django import template
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from rooibos.access.functions import get_accesscontrols_for_object, \
    filter_by_access


register = template.Library()


@register.inclusion_tag(
    'access_effective_permissions_form.html', takes_context=True)
def effective_permissions_form(context, object):
    return {'object': object,
            'contenttype': ContentType.objects.get_for_model(object.__class__),
            'request': context['request'],
            }


@register.inclusion_tag('access_permissions_display.html', takes_context=True)
def permissions_display(context, object, emptymessage=None):
    permissions = get_accesscontrols_for_object(object)
    return {'object': object,
            'contenttype': ContentType.objects.get_for_model(object.__class__),
            'permissions': permissions,
            'emptymessage': emptymessage,
            'request': context['request'],
            }


class PermissionsModifyUrlNode(template.Node):

    def __init__(self, object):
        self.object = template.Variable(object)

    def render(self, context):
        try:
            object = self.object.resolve(context)
            ct = ContentType.objects.get_for_model(object.__class__)
            return reverse(
                'access-modify-permissions',
                args=(ct.app_label, ct.model, object.id, object.name)
            )
        except template.VariableDoesNotExist:
            return ''


@register.tag
def permissions_modify_url(parser, token):
    try:
        tag_name, object = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    return PermissionsModifyUrlNode(object)


@register.filter
def accessible_objects(user, args):
    app_model, access = args.split(',')
    app, model = app_model.split('.')
    read = 'r' in access
    write = 'w' in access
    manage = 'm' in access
    return filter_by_access(
        user,
        ContentType.objects.get(app_label=app, model=model).model_class(),
        read,
        write,
        manage
    )
