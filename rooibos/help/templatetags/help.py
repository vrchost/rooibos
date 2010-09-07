from django import template
from django.core.cache import cache
from django.conf import settings
from django.core.urlresolvers import resolve

    
register = template.Library()

@register.inclusion_tag("help_pagehelp.html")
def pagehelp(page):
    return dict(link='%s%s' % (settings.HELP_URL,  page))

@register.inclusion_tag("help_help.html")
def help(reference, text=None, tooltip=None):
    return dict(link='%s%s' % (settings.HELP_URL,  reference),
                link_text=text,
                tooltip=tooltip)
    

