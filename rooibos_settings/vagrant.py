from .base import *  # NOQA


DEBUG = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e#!poDuIJ}N,".K=H:T/4z5POb;Gl/N6$6a&,(DRAHUF5c",_p'

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mdid',
        'USER': 'mdid',
        'PASSWORD': 'mdid',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            'use_unicode': True,
            'charset': 'utf8',
        },
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

SOLR_URL = 'http://127.0.0.1:8983/solr/'

# Theme colors for use in CSS
PRIMARY_COLOR = "rgb(152, 229, 198)"
SECONDARY_COLOR = "rgb(118, 167, 154)"

USE_X_FORWARDED_HOST = True
