import re
from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable, Template
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson
from django.conf import settings
from rooibos.contrib.tagging.models import Tag
from rooibos.data.models import Record, Collection
from rooibos.presentation.models import Presentation
from rooibos.util.models import OwnedWrapper
from rooibos.access import filter_by_access
from rooibos.userprofile.views import load_settings, store_settings
from rooibos.ui.functions import fetch_current_presentation, store_current_presentation
from base64 import b32encode, b64encode
import os
import glob

register = template.Library()

@register.inclusion_tag('ui_record.html', takes_context=True)
def record(context, record, selectable=False, viewmode="thumb", notitle=False):
    cpr = context['current_presentation_records']
    str(cpr)

    return {'record': record,
            'notitle': notitle,
            'selectable': selectable,
            'selected': record.id in context['request'].session.get('selected_records', ()),
            'viewmode': viewmode,
            'request': context['request'],
            'record_in_current_presentation': record.id in cpr,
            }

@register.simple_tag
def dir2(var):
    return dir(var)

@register.filter
def base32(value, filler='='):
    return b32encode(str(value)).replace('=', filler)

@register.filter
def base64(value, filler='='):
    return b64encode(str(value)).replace('=', filler)

@register.filter
def scale(value, params):
    try:
        omin, omax, nmin, nmax = map(float, params.split())
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
                ownedwrapper = OwnedWrapper.objects.get_for_object(user, object)
                context[self.var_name] = Tag.objects.get_for_object(ownedwrapper)
        else:
            qs = OwnedWrapper.objects.filter(object_id=object.id, content_type=OwnedWrapper.t(object.__class__))
            if not user.is_anonymous():
                qs = qs.exclude(user=user)
            context[self.var_name] = Tag.objects.cloud_for_queryset(qs)
        return ''

@register.tag
def owned_tags_for_object(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) (for|except) (.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    object, rule, user, var_name = m.groups()
    return OwnedTagsForObjectNode(Variable(object), Variable(user), var_name, rule == 'for')


@register.inclusion_tag('ui_tagging_form.html', takes_context=True)
def add_tags_form(context, object, tag=None, label=None):
    return {'object_id': object.id,
            'object_type': ContentType.objects.get_for_model(object.__class__).id,
            'tag': tag,
            'label': label,
            'request': context['request'],
            }


@register.inclusion_tag('ui_tag.html', takes_context=True)
def tag(context, tag, object=None, removable=False, styles=None):
    return {'object_id': object and object.id or None,
            'object_type': object and ContentType.objects.get_for_model(object.__class__).id or None,
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
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
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



@register.filter
def fileversion(file):
    """
    Takes a given file pattern and finds a matching file in the static directory.
    Used for including external libraries that have the version number
    in the file name.

    Example:

    {% url static '/flowplayer/flowplayer-*.swf'|fileversion %}

    results in

    /static/flowplayer/flowplayer-3.2.5.swf
    """
    static_dir = getattr(settings, "STATIC_DIR", None)
    if not static_dir:
        return file
    matches = glob.glob(os.path.join(static_dir, file))
    if not matches:
        return file
    return matches[0][len(os.path.commonprefix([static_dir, matches[0]])):].replace('\\', '/')
