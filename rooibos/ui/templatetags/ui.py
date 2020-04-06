import re
from django import template
from django.template import Variable
from django.contrib.contenttypes.models import ContentType
import json as simplejson
from django.conf import settings
from django.core.cache import cache
from tagging.models import Tag
from tagging.utils import calculate_cloud
from rooibos.data.models import Field
from rooibos.util.models import OwnedWrapper
from rooibos.ui.functions import fetch_current_presentation, \
    store_current_presentation
from base64 import b32encode, b64encode


register = template.Library()


@register.inclusion_tag('ui_record.html', takes_context=True)
def record(context, record, selectable=False, viewmode="thumb", notitle=False):
    cpr = context['current_presentation_records']
    str(cpr)

    extra = None
    extra_template = getattr(
        settings, 'THUMB_EXTRA_TEMPLATE', 'ui_record_extra.html')
    extra_fields = getattr(settings, 'THUMB_EXTRA_FIELDS', None)
    if extra_fields:
        thumb_extra_fields = cache.get('thumb_extra_fields')
        if not thumb_extra_fields:
            thumb_extra_fields = dict(
                Field.objects.filter(
                    label__in=extra_fields).values_list('id', 'label')
            )
            cache.set('thumb_extra_fields', thumb_extra_fields)
        if thumb_extra_fields:
            values = dict(
                (thumb_extra_fields[field], value) for field, value in
                record.fieldvalue_set.filter(
                    field__in=list(thumb_extra_fields.keys()),
                    owner=None,
                    context_type=None,
                ).order_by('-order', '-id').values_list('field', 'value')
            )
            extra = [
                (field, values[field])
                for field in extra_fields if field in values
            ]

    return {'record': record,
            'notitle': notitle,
            'selectable': selectable,
            'selected': record.id in context['request'].session.get(
                'selected_records', ()),
            'viewmode': viewmode,
            'request': context['request'],
            'record_in_current_presentation': record.id in cpr,
            'extra': extra,
            'extra_template': extra_template,
            }


@register.simple_tag
def dir2(var):
    return dir(var)


@register.filter
def base32(value, filler=b'='):
    return b32encode(str(value).encode(
        'utf8', errors='ignore')).replace(b'=', filler)


@register.filter
def base64(value, filler=b'='):
    return b64encode(value.encode(
        'utf8', errors='ignore')).replace(b'=', filler)


@register.filter
def scale(value, params):
    try:
        omin, omax, nmin, nmax = list(map(float, params.split()))
        return (float(value) - omin) / (omax - omin) * (nmax - nmin) + nmin
    except:
        return ''


class OwnedTagsForObjectNode(template.Node):

    def __init__(self, object, user, var_name, include=True):
        self.object = object
        self.user = user
        self.var_name = var_name
        self.include = include

    def render(self, context):
        object = self.object.resolve(context)
        user = self.user.resolve(context)
        if self.include:
            if not user.is_anonymous():
                ownedwrapper = OwnedWrapper.objects.get_for_object(
                    user, object)
                context[self.var_name] = Tag.objects.get_for_object(
                    ownedwrapper)
        else:
            qs = OwnedWrapper.objects.filter(
                object_id=object.id,
                content_type=OwnedWrapper.t(object.__class__)
            )
            if not user.is_anonymous():
                qs = qs.exclude(user=user)

            tags = list(Tag.objects.usage_for_queryset(qs, counts=True))
            context[self.var_name] = calculate_cloud(tags)

        return ''


@register.tag
def owned_tags_for_object(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r'(.*?) (for|except) (.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    object, rule, user, var_name = m.groups()
    return OwnedTagsForObjectNode(
        Variable(object), Variable(user), var_name, rule == 'for')


@register.inclusion_tag('ui_tagging_form.html', takes_context=True)
def add_tags_form(context, object, tag=None, label=None):
    return {
        'object_id': object.id,
        'object_type': ContentType.objects.get_for_model(object.__class__).id,
        'tag': tag,
        'label': label,
        'request': context['request'],
    }


@register.inclusion_tag('ui_tag.html', takes_context=True)
def tag(context, tag, object=None, removable=False, styles=None):
    return {
        'object_id': object and object.id or None,
        'object_type': object and ContentType.objects.get_for_model(
            object.__class__).id or None,
        'tag': tag,
        'removable': removable,
        'styles': styles,
        'request': context['request'],
    }


# Keep track of most recently edited presentation

class RecentPresentationNode(template.Node):

    def __init__(self, user, var_name):
        self.user = user
        self.var_name = var_name

    def render(self, context):
        user = self.user.resolve(context)
        context[self.var_name] = fetch_current_presentation(user)
        return ''


@register.tag
def recent_presentation(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    user, var_name = m.groups()
    return RecentPresentationNode(Variable(user), var_name)


@register.simple_tag
def store_recent_presentation(user, presentation):
    store_current_presentation(user, presentation)
    return ''


# The following is based on http://www.djangosnippets.org/snippets/829/

class VariablesNode(template.Node):
    def __init__(self, nodelist, var_name):
        self.nodelist = nodelist
        self.var_name = var_name

    def render(self, context):
        source = self.nodelist.render(context)
        context[self.var_name] = simplejson.loads(source)
        return ''


@register.tag(name='var')
def do_variables(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        msg = '"%s" tag requires arguments' % token.contents.split()[0]
        raise template.TemplateSyntaxError(msg)
    m = re.search(r'as (\w+)', arg)
    if m:
        var_name, = m.groups()
    else:
        msg = '"%s" tag had invalid arguments' % tag_name
        raise template.TemplateSyntaxError(msg)

    nodelist = parser.parse(('endvar',))
    parser.delete_first_token()
    return VariablesNode(nodelist, var_name)
