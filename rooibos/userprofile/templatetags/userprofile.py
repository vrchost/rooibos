import re
from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable, Template
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson
from rooibos.contrib.tagging.models import Tag
from rooibos.data.models import Record
from rooibos.util.models import OwnedWrapper
from rooibos.userprofile.models import UserProfile

register = template.Library()

class ProfileSettingsNode(template.Node):
    def __init__(self, filter):
        self.filter = filter
    def render(self, context):
        user = context['request'].user
        if user.is_authenticated():
            try:
                profile = user.get_profile()
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)    
            if self.filter:
                preferences = profile.preferences.filter(setting__istartswith=self.filter)
            else:
                preferences = profile.preferences.all()
            settings = dict()
            for setting in preferences:
                settings[setting.setting] = setting.value
            result = simplejson.dumps(settings)
        else:
            result = '{}';
        return result
        
    
@register.tag
def profile_settings(parser, token):
    try:
        tag_name, filter = token.contents.split(None, 1)
    except ValueError:
        tag_name = token.contents
        filter = None
    return ProfileSettingsNode(filter)
