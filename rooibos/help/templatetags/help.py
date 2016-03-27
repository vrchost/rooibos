from django import template
from django.conf import settings


register = template.Library()


def help_url_with_context(context, help_url=None):
    url = help_url or getattr(settings, 'HELP_URL', 'http://mdid.org/help/')
    if url.endswith('?') or url.endswith('/'):
        url += context
    return url


@register.inclusion_tag("help_pagehelp.html")
def pagehelp(page):
    return dict(link=help_url_with_context(page))


@register.inclusion_tag("help_help.html")
def help(reference, text=None, tooltip=None):
    return dict(link=help_url_with_context(reference),
                link_text=text,
                tooltip=tooltip)
