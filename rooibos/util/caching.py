from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.conf import settings

TIMEOUT = 10 * 60  # 10 minutes
KEY_PREFIX = getattr(settings, "CACHE_KEY_PREFIX", "")

def get_model_id(model):
    return ContentType.objects.get_for_model(model).id

def get_model_key(model):
    return '%smodel_cache_version_%d' % (KEY_PREFIX, get_model_id(model))

def incr_model_version(model):
    key = get_model_key(model)
    try:
        version = cache.incr(key)
    except ValueError:
        # keep versions cached longer than regular items
        cache.add(key, 0, timeout=TIMEOUT + 60)
        try:
            version = cache.incr(key)
        except ValueError:
            # Caching is not available, can return anything
            version = 1
    return version

invalidate_model_cache = incr_model_version

def incr_model_version_post_event(sender, **kwargs):
    incr_model_version(sender)

post_save.connect(incr_model_version_post_event)
post_delete.connect(incr_model_version_post_event)

def incr_model_version_post_event_m2m(sender, **kwargs):
    if not kwargs['action'].startswith('post'):
        return
    incr_model_version(sender)
    incr_model_version(kwargs.get('instance').__class__)
    incr_model_version(kwargs.get('model'))

m2m_changed.connect(incr_model_version_post_event_m2m)


def get_model_version(model):
    return cache.get(get_model_key(model)) or incr_model_version(model)

def key_suffix(models):
    return ''.join('$%d.%d' % (get_model_id(model), get_model_version(model))
                   for model in models) if models else ''

def version_cache_key(key, models):
    return KEY_PREFIX + key + key_suffix(models)

def cache_get(key, model_dependencies=None, default=None):
    return cache.get(version_cache_key(key, model_dependencies), default)

def cache_set(key, value, model_dependencies=None):
    cache.set(version_cache_key(key, model_dependencies), value, timeout=TIMEOUT)

def cache_get_many(keys, model_dependencies=None):
    values = cache.get_many(version_cache_key(key, model_dependencies) for key in keys)
    prefix_length = len(KEY_PREFIX)
    suffix_length = -len(key_suffix(model_dependencies)) if model_dependencies else None
    return dict((key[prefix_length:suffix_length], value)
                for (key, value) in values.iteritems())

def cache_set_many(values, model_dependencies=None):
    cache.set_many(dict((version_cache_key(key, model_dependencies), value)
                        for (key, value) in values.iteritems()), timeout=TIMEOUT)



def get_cached_value(key, func, model_dependencies=None):
    value = cache_get(key, model_dependencies)
    if value == None:
        value = func()
        if value != None:
            cache_set(key, value, model_dependencies)
    return value
