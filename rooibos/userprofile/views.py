from django.views.decorators.cache import cache_control
from rooibos.util import json_view
from models import UserProfile, Preference


def load_settings(user, filter=None):
    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    settings = dict()
    if filter:
        preferences = profile.preferences.filter(setting__startswith=filter)
    else:
        preferences = profile.preferences.all()
    for setting in preferences:
        settings.setdefault(setting.setting, []).append(setting.value)
    return settings
    
def store_settings(user, key, value):
    try:
        profile = user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if key and value:
        setting, created = profile.preferences.get_or_create(setting=key)
        setting.value = value
        setting.save()
        return True
        
    return False

@json_view
def load_settings_view(request, filter=None):
    if not request.user.is_authenticated():
        return dict(error='Not logged in')
    return dict(settings=load_settings(request.user, filter))
    

@json_view
def store_settings_view(request):
    if not request.user.is_authenticated():
        return dict(error='Not logged in')
    result = store_settings(request.user, request.POST.get('key'), request.POST.get('value'))
    return dict(message='Saved' if result else 'No key/value provided')
