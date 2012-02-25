# DON'T PUT ANY LOCALIZED SETTINGS OR SECRETS IN THIS FILE
# they should go in settings_local.py instead
# with a blank setting in settings_local.template.py

import os
import sys

install_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
lib_dir = os.path.join(install_dir, 'rooibos', 'contrib')

if not install_dir in sys.path: sys.path.append(install_dir)
if not lib_dir in sys.path: sys.path.append(lib_dir)

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
MEDIA_URL = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
#    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "rooibos.context_processors.settings",
    "rooibos.context_processors.selected_records",
    "rooibos.context_processors.current_presentation",
)

MIDDLEWARE_CLASSES = (
    'rooibos.middleware.Middleware',
    'rooibos.help.middleware.PageHelp',
#    'rooibos.profile_middleware.ProfileMiddleware',
    'rooibos.sslredirect.SSLRedirect',
    'rooibos.ui.middleware.PageTitles',
    'django.middleware.common.CommonMiddleware',
    'rooibos.util.stats_middleware.StatsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'rooibos.api.middleware.CookielessSessionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'djangologging.middleware.LoggingMiddleware',
    'djangologging.middleware.SuppressLoggingOnAjaxRequestsMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'rooibos.storage.middleware.StorageOnStart',
    'rooibos.access.middleware.AccessOnStart',
    'rooibos.middleware.HistoryMiddleware',
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
    'django_extensions',
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
    'rooibos.federatedsearch.nasa',
    'rooibos.converters',
    'rooibos.contrib.tagging',
    'rooibos.workers',
    'rooibos.userprofile',
    'rooibos.mediaviewer',
    'rooibos.megazine',
    'rooibos.groupmanager',
    'rooibos.pdfviewer',
    'rooibos.pptexport',
    'rooibos.audiotextsync',
    'pagination',
    'impersonate',
    'compressor',
    'south',
)

STORAGE_SYSTEMS = {
    'local': 'rooibos.storage.localfs.LocalFileSystemStorageSystem',
    'online': 'rooibos.storage.online.OnlineStorageSystem',
    'pseudostreaming': 'rooibos.storage.pseudostreaming.PseudoStreamingStorageSystem',
}

GROUP_MANAGERS = {
    'nasaimageexchange': 'rooibos.federatedsearch.nasa.nix.NasaImageExchange',
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

STATIC_DIR = os.path.join(install_dir, 'rooibos', 'static')

FFMPEG_EXECUTABLE = os.path.join(install_dir, 'dist', 'windows', 'ffmpeg', 'bin', 'ffmpeg.exe')

PDF_PAGESIZE = 'letter'  # 'A4'

additional_settings = [
    'settings_local',
]

additional_settings.extend(filter(None, os.environ.get('ROOIBOS_ADDITIONAL_SETTINGS', '').split(';')))

# Load settings for additional applications


while additional_settings:
    settings = additional_settings.pop(0)
    module = __import__(settings, globals(), locals(), 'rooibos')
    for setting in dir(module):
        if setting == setting.upper():
            if locals().has_key(setting):
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
