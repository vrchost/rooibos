import tempfile
from .base import *  # NOQA
from .base import _get_log_handler


DEBUG = False
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED = DEBUG

SECRET_KEY = 'not secret'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.sqlite',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {},
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

SCRATCH_DIR = tempfile.mkdtemp()
print "USING SCRATCH_DIR:", SCRATCH_DIR

LOGGING['handlers'] = _get_log_handler(SCRATCH_DIR)
