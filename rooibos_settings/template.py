from .base import *  # NOQA

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e#!poDuIJ}N,".K=H:T/4z5POb;Gl/N6$6a&,(DRAHUF5c",_p'

# Add the hostname of your server, or keep '*' to allow all host names
ALLOWED_HOSTS = ['*']

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mdid',
        'USER': 'mdid',
        'PASSWORD': 'rooibos',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            'use_unicode': True,
            'charset': 'utf8',
        },
    }
}

RABBITMQ_OPTIONS = {
    'host': 'localhost',
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

SOLR_URL = 'http://127.0.0.1:8983/solr/mdid'
SOLR_RECORD_INDEXER = None
SOLR_RECORD_PRE_INDEXER = None


# Theme colors for use in CSS
PRIMARY_COLOR = "rgb(152, 189, 198)"
SECONDARY_COLOR = "rgb(118, 147, 154)"


# Enter your Flickr API credentials
# FLICKR_KEY = ''
# FLICKR_SECRET = ''

# Uncomment if you subscribe to ARTstor
# ARTSTOR_GATEWAY = 'http://sru.artstor.org/SRU/artstor.htm'


# Uncomment and complete relevant user authentication settings

# LDAP_AUTH = (
#     {
#         # LDAP Example
#         'uri': 'ldap://ldap.example.edu',
#         'base': 'ou=People,o=example',
#         'cn': 'cn',
#         'dn': 'dn',
#         'version': 2,
#         'scope': 1,
#         'options': {'OPT_X_TLS_TRY': 1},
#         'attributes': (
#             'sn', 'mail', 'givenName', 'eduPersonPrimaryAffiliation'),
#         'firstname': 'givenname',
#         'lastname': 'sn',
#         'email': 'mail',
#         'bind_user': '',
#         'bind_password': '',
#         # list of groups to check for user membership;
#         # populates virtual LDAP attribute '_groups'
#         'groups': (),
#     },
#     {
#         # Active Directory Example
#         'uri': 'ldap://ad.example.edu',
#         'base': 'OU=users,DC=ad,DC=example,DC=edu',
#         'cn': 'sAMAccountName',
#         'dn': 'distinguishedName',
#         'version': 3,
#         'scope': 2,  # ldap.SCOPE_SUBTREE
#         'options': {
#             'OPT_X_TLS_TRY': 1,
#             'OPT_REFERRALS': 0,
#         },
#         'attributes': ('sn', 'mail', 'givenName', 'eduPersonAffiliation'),
#         'firstname': 'givenName',
#         'lastname': 'sn',
#         'email': 'mail',
#         'bind_user': 'CN=LDAP Bind user,OU=users,DC=ad,DC=jmu,DC=edu',
#         'bind_password': 'abc123',
#         'domain': 'ad.example.com',
#         'email_default': '%s@example.com',  # user name will replace %s
#         # list of groups to check for user membership;
#         # populates virtual LDAP attribute '_groups'
#         'groups': ('CN=Sample Group,OU=groups,DC=ad,DC=jmu,DC=edu',),
#     },
#
# )

# IMAP_AUTH = (
#     {
#         'server': 'imap.example.edu',
#         'port': 993,
#         'domain': 'example.edu',
#         'secure': True,
#     },
# )

# POP_AUTH = (
#     {
#         'server': 'pop.gmail.com',
#         'port': 995,
#         'domain': 'gmail.com',
#         'secure': True,
#     },
# )


# Adjust path to ffmpeg if necessary
# FFMPEG_EXECUTABLE = '/usr/bin/ffmpeg'
