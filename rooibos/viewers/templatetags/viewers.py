from django import template
from rooibos.viewers import get_viewers_for_object


register = template.Library()


@register.inclusion_tag('viewers_list.html', takes_context=True)
def list_viewers(context, obj, next_url=None, separator=', '):
    viewers = get_viewers_for_object(obj, context['request'])
    viewers = sorted(
        viewers, key=lambda v: getattr(v, 'weight', 0), reverse=True)

    return {
        'obj': obj,
        'viewers': viewers,
        'next': next_url,
        'separator': separator,
    }
