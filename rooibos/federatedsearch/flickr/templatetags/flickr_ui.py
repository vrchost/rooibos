import re
from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable
from django.contrib.contenttypes.models import ContentType
from rooibos.contrib.tagging.models import Tag
from models import FlickrSearch
from rooibos.util.models import OwnedWrapper

register = template.Library()

@register.inclusion_tag('flicker_ui.html', takes_context=True)
def photo(context, photo, selectable=False, viewmode="thumb"):
    return {'photo': photo,
            'selectable': selectable,
            'selected': (photo['id'] + '|' + photo['title']) in context['request'].session.get('selected_flickrs', ()),
            'viewmode': viewmode,
            }
