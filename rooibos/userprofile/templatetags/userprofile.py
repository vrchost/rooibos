from django import template
import json as simplejson
from rooibos.userprofile.models import UserProfile
from rooibos.userprofile.views import load_settings


register = template.Library()


class ProfileSettingsNode(template.Node):

    def __init__(self, filter):
        self.filter = filter

    def render(self, context):
        user = context['request'].user if 'request' in context else None
        if user and user.is_authenticated():
            try:
                profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
            if self.filter:
                preferences = profile.preferences.filter(
                    setting__istartswith=self.filter)
            else:
                preferences = profile.preferences.all()
            settings = dict()
            for setting in preferences:
                settings[setting.setting] = setting.value
            result = simplejson.dumps(settings)
        else:
            result = '{}'
        return result


@register.tag
def profile_settings(parser, token):
    try:
        tag_name, filter = token.contents.split(None, 1)
    except ValueError:
        filter = None
    return ProfileSettingsNode(filter)


@register.filter
def profile_setting(user, setting):
    if user and user.is_authenticated():
        settings = load_settings(user, filter=setting)
        return settings.get(setting, [None])[0]
    else:
        return None
