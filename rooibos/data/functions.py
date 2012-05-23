from rooibos.userprofile.views import load_settings, store_settings


COLLECTION_VISIBILITY_PREFERENCES = 'data_collection_visibility_prefs'

def get_collection_visibility_preferences(user):
    setting = load_settings(user, COLLECTION_VISIBILITY_PREFERENCES).get(
        COLLECTION_VISIBILITY_PREFERENCES, ['show:']
    )
    try:
        mode, ids = setting[0].split(':')
        ids = map(int, ids.split(',')) if ids else []
    except ValueError:
        mode = 'show'
        ids = []
    return mode, ids

def set_collection_visibility_preferences(user, mode, ids):
    value = '%s:%s' % (mode, ','.join(ids))
    return store_settings(user,
                          COLLECTION_VISIBILITY_PREFERENCES,
                          value)

def apply_collection_visibility_preferences(user, queryset):
    mode, ids = get_collection_visibility_preferences(user)
    if mode == 'show':
        return queryset.exclude(id__in=ids)
    else:
        return queryset.filter(id__in=ids)
