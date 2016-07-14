# DON'T PUT ANY LOCALIZED SETTINGS OR SECRETS IN THIS FILE
# they should go in settings_local.py instead
# with a blank setting in settings_local.template.py

import os
import sys
import re


install_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(install_dir, 'rooibos', 'contrib')

if install_dir not in sys.path:
    sys.path.append(install_dir)
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

USE_ETAGS = False

# When set to True, may cause problems with basket functionality
SESSION_SAVE_EVERY_REQUEST = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media-unused/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "rooibos.context_processors.settings",
    "rooibos.context_processors.selected_records",
    "rooibos.context_processors.current_presentation",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.http.ConditionalGetMiddleware',
    'rooibos.middleware.Middleware',
    'rooibos.help.middleware.PageHelp',
    'rooibos.sslredirect.SSLRedirect',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'rooibos.api.middleware.CookielessSessionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'rooibos.ui.middleware.PageTitles',
    'pagination.middleware.PaginationMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'rooibos.storage.middleware.StorageOnStart',
    'rooibos.access.middleware.AccessOnStart',
    'rooibos.data.middleware.DataOnStart',
    'rooibos.middleware.HistoryMiddleware',
    'rooibos.access.middleware.AnonymousIpGroupMembershipMiddleware',
)

ROOT_URLCONF = 'rooibos.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.comments',
    'django.contrib.redirects',
    'django.contrib.staticfiles',
    'django_extensions',
    'tagging',
    'google_analytics',
    'rooibos.data',
    'rooibos.migration',
    'rooibos.util',
    'rooibos.access',
    'rooibos.solr',
    'rooibos.storage',
    'rooibos.legacy',
    'rooibos.ui',
    'rooibos.viewers',
    'rooibos.help',
    'rooibos.presentation',
    'rooibos.statistics',
    'rooibos.federatedsearch',
    'rooibos.federatedsearch.artstor',
    'rooibos.federatedsearch.flickr',
    'rooibos.federatedsearch.shared',
    'rooibos.workers',
    'rooibos.userprofile',
    'rooibos.mediaviewer',
    'rooibos.megazine',
    'rooibos.groupmanager',
    'rooibos.pdfviewer',
    'rooibos.pptexport',
    'pagination',
    'impersonate',
    'compressor',
    'south',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

STORAGE_SYSTEMS = {
    'local': 'rooibos.storage.localfs.LocalFileSystemStorageSystem',
    'online': 'rooibos.storage.online.OnlineStorageSystem',
    'pseudostreaming':
        'rooibos.storage.pseudostreaming.PseudoStreamingStorageSystem',
    's3': 'rooibos.storage.s3.S3StorageSystem',
}

GROUP_MANAGERS = {
}

AUTH_PROFILE_MODULE = 'userprofile.UserProfile'

WEBSERVICE_NAMESPACE = "http://mdid.jmu.edu/webservices"

# Methods to be called after a user is successfully authenticated
# using an external backend (LDAP, IMAP, POP).
# Must take two parameters:
#   user object
#   dict of string->list/tuple pairs (may be None or empty)
# Returns:
#   True: login continues
#   False: login rejected, try additional login backends if available
LOGIN_CHECKS = (
    'rooibos.access.models.update_membership_by_attributes',
)

TEMPLATE_DIRS = (
    os.path.join(install_dir, 'rooibos', 'templates'),
)

STATICFILES_DIRS = [
    os.path.join(install_dir, 'rooibos', 'static'),
]
STATIC_URL = '/static/'


FFMPEG_EXECUTABLE = os.path.join(
    install_dir, 'dist', 'windows', 'ffmpeg', 'bin', 'ffmpeg.exe')

PDF_PAGESIZE = 'letter'  # 'A4'

SHOW_FRONTPAGE_LOGIN = "yes"

MASTER_TEMPLATE = 'master_root.html'

# Settings that should be available in template rendering
EXPOSE_TO_CONTEXT = (
    'STATIC_DIR',
    'PRIMARY_COLOR',
    'SECONDARY_COLOR',
    'CUSTOM_TRACKER_HTML',
    'ADMINS',
    'LOGO_URL',
    'FAVICON_URL',
    'COPYRIGHT',
    'TITLE',
    'SHOW_FRONTPAGE_LOGIN',
    'MASTER_TEMPLATE',
    'PREVIEW_WIDTH',
    'PREVIEW_HEIGHT',
    'SHOW_TERMS',
    'SHIB_ENABLED',
    'SHIB_LOGOUT_URL',
    'HIDE_SHOWCASES',
)


additional_settings = [
    'settings_local',
]

additional_settings.extend(
    filter(None, os.environ.get('ROOIBOS_ADDITIONAL_SETTINGS', '').split(';')))

# Load settings for additional applications


while additional_settings:
    settings = additional_settings.pop(0)
    module = __import__(settings, globals(), locals(), 'rooibos')
    for setting in dir(module):
        if setting == setting.upper():
            if setting in locals():
                if isinstance(locals()[setting], dict):
                    locals()[setting].update(getattr(module, setting))
                elif isinstance(locals()[setting], tuple):
                    locals()[setting] += (getattr(module, setting))
                else:
                    locals()[setting] = getattr(module, setting)
            else:
                locals()[setting] = getattr(module, setting)
        elif setting == 'additional_settings':
            additional_settings[:0] = getattr(module, setting)
        elif setting == 'remove_settings':
            for remove_setting in getattr(module, setting):
                del locals()[remove_setting]


# set logging if not already defined (doing this after importing
# settings_local to be able to refer to the LOG_DIR configured there

def _get_log_handler():

    # Can't do sys.argv since it does not exist when running under PyISAPIe
    cmdline = getattr(sys, 'argv', [])
    if len(cmdline) > 1:
        # only use first command line argument for log file name
        basename = 'rooibos-%s' % '-'.join(
            re.sub(r'[^a-zA-Z0-9]', '', x) for x in cmdline[1:2])
    else:
        basename = 'rooibos'

    try:
        return {
            'file': {
                'class': 'logging.FileHandler',
                'filename': os.path.join(LOG_DIR, basename +'.log'),
                'formatter': 'verbose',
            },
        }
    except NameError:
        return {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            }
        }

try:
    LOGGING
except NameError:
    handler = _get_log_handler()
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[%(name)30.30s]%(levelname)8s %(asctime)s '
                          '%(process)d %(message)s '
                          '[%(filename)s:%(lineno)d]'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': handler,
        'loggers': {
            'rooibos': {
                'handlers': [handler.keys()[0]],
                'level': 'DEBUG',
                'propagate': False,
            },
            'pika': {
                'handlers': [handler.keys()[0]],
                'level': 'WARNING',
            },
            '': {
                'handlers': [handler.keys()[0]],
                'level': 'DEBUG',
            },
        },
    }


# Build required DATABASES structure
try:
    DATABASES
except NameError:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.' + DATABASE_ENGINE,
            'NAME': DATABASE_NAME,
            'USER': DATABASE_USER,
            'PASSWORD': DATABASE_PASSWORD,
            'HOST': DATABASE_HOST,
            'PORT': DATABASE_PORT,
            'OPTIONS': DATABASE_OPTIONS,
        }
    }
