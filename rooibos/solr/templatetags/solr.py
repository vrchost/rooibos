from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
@stringfilter
def quoteterm(term):
    return '"%s"' % term if ' ' in term else term
