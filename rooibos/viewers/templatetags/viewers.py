from django import template
from django.core.urlresolvers import reverse
from rooibos.storage.models import Media
from rooibos.viewers import get_viewers_for_object


register = template.Library()

#@register.simple_tag
#def view_inline(obj):
#    viewers = get_viewers_for_object(obj, None, inline=True)
#    # Todo: don't just pick first one
#    # Todo: use current user from context to check permissions
#    return viewers and viewers[0].inline(obj) or ''


#@register.inclusion_tag('viewers_list.html', takes_context=True)
#def list_viewers(context, obj, next_url=None, separator=', '):
#    viewers = []
#    for viewer in get_viewers_for_object(obj, user=context['request'].user):
#        viewers.append((viewer, hasattr(viewer, 'url_for_obj') and viewer.url_for_obj(obj) or None))
#    viewers = sorted(viewers, key=lambda v: getattr(v[0], 'weight', 0), reverse=True)
#
#    return {'obj': obj,
#            'viewers': viewers,
#            'next': next_url,
#            'separator': separator,
#            }


@register.inclusion_tag('viewers_list.html', takes_context=True)
def list_viewers(context, obj, next_url=None, separator=', '):
    viewers = get_viewers_for_object(obj, context['request'])
    viewers = sorted(viewers, key=lambda v: getattr(v, 'weight', 0), reverse=True)

    return {'obj': obj,
            'viewers': viewers,
            'next': next_url,
            'separator': separator,
            }
