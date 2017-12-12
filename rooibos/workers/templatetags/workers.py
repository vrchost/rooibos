from django import template
from django.utils.safestring import SafeString
from django.core.urlresolvers import reverse
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
        for key, value in data.iteritems():
            if key == 'attachment':
                key = '<strong>Download</strong>'
                name = os.path.split(value)[1]
                url = reverse(
                    'workers-download-attachment', kwargs=dict(url=name))
                value = '<a href="%s" target="_blank">%s</a>' % (
                    url, name)
            lines.append('%s: %s<br />' % (key, value))
        return SafeString(''.join(lines))
    except (AttributeError, TypeError):
        return result
