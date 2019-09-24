from django import template
from django.utils.safestring import SafeString
from django.core.urlresolvers import reverse, NoReverseMatch
import json
import os


register = template.Library()


@register.filter
def format_worker_result(result):
    try:
        data = json.loads(result)
    except ValueError:
        return result
    lines = []
    try:
        if 'exc_message' in data and 'exc_type' in data:
            return SafeString(
                '<strong>%(exc_type)s:</strong> %(exc_message)s' % data)
        for key, value in data.items():
            if key == 'attachment':
                key = '<strong>Download</strong>'
                name = os.path.split(value)[1]
                url = reverse(
                    'workers-download-attachment', kwargs=dict(url=name))
                value = '<a href="%s" target="_blank">%s</a>' % (
                    url, name)
            lines.append('%s: %s<br />' % (key, value))
        return SafeString(''.join(lines))
    except (AttributeError, TypeError, NoReverseMatch):
        return result


@register.filter
def format_worker_args(result):
    try:
        data = json.loads(result)
        if 'args' not in data or 'kwargs' not in data:
            return result
    except (ValueError, TypeError):
        return result

    lines = [repr(arg) for arg in data['args']] + [
        '<strong class="job-arg">%s:</strong> '
        '<span class="job-arg-value">%s</span>' % (key, value)
        for key, value in data['kwargs'].items()
    ]
    return SafeString('<br />'.join(lines))
