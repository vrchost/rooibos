from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable
from rooibos.statistics import get_history
from datetime import datetime, timedelta

register = template.Library()


def scale(list):
    m = max(list)
    if m == 0:
        return list
    else:
        return map(lambda v: int(v * 100 / m), list)

@register.simple_tag
def past_week_graph(event, object=None):
    history = get_history(event, from_date=datetime.now().date() - timedelta(6), object=object)
    data = ','.join(map(str, scale(history)))
    url = 'http://chart.apis.google.com/chart?chs=150x50&cht=ls&chd=t:%s' % data
    return '<img src="%s" width="150" height"50" />' % url
    
