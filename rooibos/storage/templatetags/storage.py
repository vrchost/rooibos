import re
from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable
from rooibos.storage.models import Storage
from rooibos.access import filter_by_access


register = template.Library()
