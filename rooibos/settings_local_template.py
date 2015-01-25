DEBUG = True
TEMPLATE_DEBUG = DEBUG
#LOGGING_OUTPUT_ENABLED = True

INSTANCE_NAME = ''

# Needed to enable compression JS and CSS files
COMPRESS = True
MEDIA_URL = '/static/'
MEDIA_ROOT = 'd:/mdid/rooibos/static/'


ADMINS = (
#    ('Your name', 'your@email.example'),
)

MANAGERS = ADMINS

# Settings for MySQL
DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_OPTIONS = {
    'use_unicode': True,
    'charset': 'utf8',
}

# Settings for Microsoft SQL Server (use the appropriate driver setting)
#DATABASE_ENGINE = 'sql_server.pyodbc'
#DATABASE_OPTIONS= {
#    'driver': 'SQL Native Client',             # FOR SQL SERVER 2005
#    'driver': 'SQL Server Native Client 10.0', # FOR SQL SERVER 2008
#    'MARS_Connection': True,
#}

# Settings for all database systems
DATABASE_NAME = 'rooibos'             # Or path to database file if using sqlite3.
DATABASE_USER = 'rooibos'             # Not used with sqlite3.
DATABASE_PASSWORD = 'rooibos'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

DEFAULT_CHARSET = 'utf-8'
DATABASE_CHARSET = 'utf8'

CLOUDFILES_USERNAME = ''
CLOUDFILES_API_KEY = ''

# S3 settings
S3_FOLDER_MAPPING = {}
AWS_STORAGE_BUCKET_NAME = ''
AWS_ACCESS_KEY = None
AWS_SECRET_KEY = None

CDN_THUMBNAILS = {}

UPLOAD_LIMIT = 5 * 1024 * 1024

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e#!poDuIJ}N,".K=H:T/4z5POb;Gl/N6$6a&,(DRAHUF5c",_p'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

SOLR_URL = 'http://127.0.0.1:8983/solr/'
SOLR_RECORD_INDEXER = None

SCRATCH_DIR = 'c:/mdid-scratch/'
AUTO_STORAGE_DIR = 'c:/mdid-collections/'
LOG_DIR = 'c:/mdid-log/'

# File upload size limit in bytes (default 5 MB)
UPLOAD_LIMIT = 5 * 1024 * 1024

# Legacy setting for ImageViewer 2 support
SECURE_LOGIN = False


LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/'

CACHE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'memcached://127.0.0.1:11211/',
        'KEY_PREFIX': INSTANCE_NAME,
    }
}

INTERNAL_IPS = ('127.0.0.1',)

# If HELP_URL ends in / or ?, the current page id or reference will be appended
HELP_URL = 'http://mdid.org/help/'

DEFAULT_LANGUAGE = 'en-us'

GOOGLE_ANALYTICS_MODEL = True

FLICKR_KEY = ''
FLICKR_SECRET = ''

# Set to None if you don't subscribe to ARTstor
ARTSTOR_GATEWAY = None
#ARTSTOR_GATEWAY = 'http://sru.artstor.org/SRU/artstor.htm'

OPEN_OFFICE_PATH = 'C:/Program Files/OpenOffice.org 3/program/'

GEARMAN_SERVERS = ['127.0.0.1']

AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)
#    'django_cas.backends.CASBackend',
#    'rooibos.auth.ldapauth.LdapAuthenticationBackend',
#    'rooibos.auth.mailauth.ImapAuthenticationBackend',
#    'rooibos.auth.mailauth.PopAuthenticationBackend',


CAS_SERVER_URL = None

MIDDLEWARE_CLASSES = ('rooibos.auth.middleware.BasicAuthenticationMiddleware',)

LDAP_AUTH = (
    {
        # LDAP Example
        'uri': 'ldap://ldap.example.edu',
        'base': 'ou=People,o=example',
        'cn': 'cn',
        'dn': 'dn',
        'version': 2,
        'scope': 1,
        'options': {'OPT_X_TLS_TRY': 1},
        'attributes': ('sn', 'mail', 'givenName', 'eduPersonPrimaryAffiliation'),
        'firstname': 'givenname',
        'lastname': 'sn',
        'email': 'mail',
        'bind_user': '',
        'bind_password': '',
        # list of groups to check for user membership;
        # populates virtual LDAP attribute '_groups'
        'groups': (),
    },
    {
        # Active Directory Example
        'uri': 'ldap://ad.example.edu',
        'base': 'OU=users,DC=ad,DC=example,DC=edu',
        'cn': 'sAMAccountName',
        'dn': 'distinguishedName',
        'version': 3,
        'scope': 2, # ldap.SCOPE_SUBTREE
        'options': {
            'OPT_X_TLS_TRY': 1,
            'OPT_REFERRALS': 0,
            },
        'attributes': ('sn', 'mail', 'givenName', 'eduPersonAffiliation'),
        'firstname': 'givenName',
        'lastname': 'sn',
        'email': 'mail',
        'bind_user': 'CN=LDAP Bind user,OU=users,DC=ad,DC=jmu,DC=edu',
        'bind_password': 'abc123',
        'domain': 'ad.example.com',
        'email_default': '%s@example.com',  # user name will replace %s
        # list of groups to check for user membership;
        # populates virtual LDAP attribute '_groups'
        'groups': ('CN=Sample Group,OU=groups,DC=ad,DC=jmu,DC=edu',),
    },

)

IMAP_AUTH = (
    {
        'server': 'imap.example.edu',
        'port': 993,
        'domain': 'example.edu',
        'secure': True,
    },
)

POP_AUTH = (
    {
        'server': 'pop.gmail.com',
        'port': 995,
        'domain': 'gmail.com',
        'secure': True,
    },
)

SESSION_COOKIE_AGE = 6 * 3600  # in seconds

SHIB_ENABLED = False
SHIB_ATTRIBUTE_MAP = None
SHIB_USERNAME = None
SHIB_EMAIL = None
SHIB_FIRST_NAME = None
SHIB_LAST_NAME = None
SHIB_LOGOUT_URL = None

SSL_PORT = None  # ':443'

# Theme colors for use in CSS
PRIMARY_COLOR = "rgb(152, 189, 198)"
SECONDARY_COLOR = "rgb(118, 147, 154)"

LOGO_URL = None
FAVICON_URL = None
COPYRIGHT = None
TITLE = None

WWW_AUTHENTICATION_REALM = "Please log in to access media from MDID at Your University"

CUSTOM_TRACKER_HTML = ""

SHOW_FRONTPAGE_LOGIN = 'yes'

EXPOSE_TO_CONTEXT = ('STATIC_DIR', 'PRIMARY_COLOR', 'SECONDARY_COLOR', 'CUSTOM_TRACKER_HTML', 'ADMINS', 'LOGO_URL', 'FAVICON_URL', 'COPYRIGHT', 'CAS_SERVER_URL',)


# The Megazine viewer is using a third party component that has commercial
# licensing requirements.  To enable the component you need to enter your
# license key, which is available for free for educational institutions.
# See static/megazine/COPYING.
MEGAZINE_PUBLIC_KEY = ""

# To use a commercial licensed flowplayer, enter your flowplayer key here
# and add the flowplayer.commercial-3.x.x.swf file to the
# rooibos/static/flowplayer directory
FLOWPLAYER_KEY = ""

# MDID uses some Yahoo APIs that require an application key
# You can get one at https://developer.apps.yahoo.com/dashboard/createKey.html
YAHOO_APPLICATION_ID = ""


# By default, video delivery links are created as symbolic links. Some streaming
# servers (e.g. Wowza) don't deliver those, so hard links are required.
HARD_VIDEO_DELIVERY_LINKS = False


# List of facets to permanently hide in Explore screen
# Comparison is made on effective (shown) label
HIDE_FACETS = ()
# List of facets using whole expression instead of tokenized terms
# Comparison is made on effective (shown) label
FULL_FACETS = ()


PREVIEW_WIDTH = 640
PREVIEW_HEIGHT = 480


# If the JPEGs available to MDID are not compressed properly, loading a presentation
# may take a very long time, as a lot of large images have to be transferred.  By
# setting this, presentation images are forces to be reprocessed and compressed to
# the usual 85% quality
FORCE_SLIDE_REPROCESS = False


# If set to a list of strings, all groups with the given names are granted read
# access on newly created presentations
PRESENTATION_PERMISSIONS = []


MASTER_TEMPLATE = 'master_root.html'


INSTALLED_APPS = ()


FFMPEG_EXECUTABLE = '/usr/bin/ffmpeg'


additional_settings = [
#    'apps.jmutube.settings_local',
#    'apps.svohp.settings_local',
]
