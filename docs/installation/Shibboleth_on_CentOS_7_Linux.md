# Installation on Ubuntu Linux

The following instructions are for CentOS 7, but
should work with minor changes on other distributions as well.

Unless noted otherwise, all commands should be run as `root`.

## Server Preparation

### Add Shibboleth repository

Create a file `/etc/yum.repos.d/shibboleth.repo` with the following
contents:
```
[security_shibboleth]
# If the mirrors stop working, change download to downloadcontent...
name=Shibboleth (CentOS_7)
type=rpm-md
baseurl=http://download.opensuse.org/repositories/security:/shibboleth/CentOS_7/
gpgcheck=1
gpgkey=http://download.opensuse.org/repositories/security:/shibboleth/CentOS_7/repodata/repomd.xml.key
enabled=1
```

### Install Packages
```
yum install httpd shibboleth
```

## Configure Shibboleth

Edit the `<ApplicationDefaults>` section in
`/etc/shibboleth/shibboleth2.xml` to reflect your Shibboleth
environment.

If you need support for additional attributes, edit
`/etc/shibboleth/attribute-map.xml` accordingly.

## Configure nginx

In `/etc/nginx/conf.d/mdid.conf`, change the `proxy_pass` line to

```
proxy_pass http://127.0.0.1:8100;
```

## Configure Apache

Create a file `/etc/httpd/conf.d/mdid.conf` with the following
contents, replacing all instances of `YOUR.DOMAIN.NAME` with the DNS name of
your MDID server:

```
<VirtualHost 127.0.0.1:8100>
        UseCanonicalName Off

        ServerName https://YOUR.DOMAIN.NAME

        DocumentRoot /home/mdid/www

        <Directory /home/mdid/www>
            Order allow,deny
            Allow from all
            Require all granted
        </Directory>

        Alias /static/ "/opt/mdid/rooibos/static/"

        ErrorLog /opt/mdid/log/apache2-error.log

        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel warn

        CustomLog /opt/mdid/log/apache2-access.log combined

        <Location /shibboleth>
                AuthType shibboleth
                ShibRequireSession On
                ShibUseHeaders On
                require valid-user
        </Location>

        ProxyPreserveHost On
        <Location />
            ProxyPass http://127.0.0.1:8001/
            ProxyPassReverse http://127.0.0.1:8001/
            RequestHeader set X-FORWARDED-PROTOCOL ssl
            RequestHeader set X-FORWARDED-SSL on
            RequestHeader set Host YOUR.DOMAIN.NAME
        </Location>

        <Location /Shibboleth.sso>
                SetHandler shib
                ProxyPass "!"
        </Location>
</VirtualHost>
```

## Configure MDID

Add the following settings to your `local_settings.py` file:

```
SHIB_ENABLED = True
SHIB_ATTRIBUTE_MAP = {
    'CUSTOM_EMAIL': (True, 'mail'),
    'CUSTOM_FIRSTNAME': (False, 'givenName'),
    'CUSTOM_LASTNAME': (False, 'sn'),
    'CUSTOM_USERNAME': (True, 'username'),
}
SHIB_USERNAME = "username"
SHIB_EMAIL = "mail"
SHIB_FIRST_NAME = "givenName"
SHIB_LAST_NAME = "sn"

MIDDLEWARE_CLASSES += ('rooibos.shib_middleware.ShibMiddleware',)

TEMPLATES[0]['OPTIONS']['context_processors'] += \
    ('rooibos.shib_contextprocessors.shibboleth',)
```

Create the file `/opt/mdid/rooibos/shib_middleware.py` with the following
content, replacing `YOUR.DOMAIN.EDU` with the domain name used in email
addresses (if applicable):
```
class ShibMiddleware(object):
    def process_request(self, request):
        if not request.META.get('HTTP_SHIB_IDENTITY_PROVIDER'):
            return
        user = request.META.get('HTTP_REMOTE_USER', '')
        if '@' in user:
            user = user.split('@')[0]
        givenname = request.META.get('HTTP_GIVENNAME') or user
        surname = request.META.get('HTTP_SURNAME') or user
        request.META['CUSTOM_USERNAME'] = user
        request.META['CUSTOM_EMAIL'] = '%s@YOUR.DOMAIN.EDU' % user
        request.META['CUSTOM_FIRSTNAME'] = givenname
        request.META['CUSTOM_LASTNAME'] = surname
```

Create the file `/opt/mdid/rooibos/shib_contextprocessors.py` with the
following content:
```
def shibboleth(request):
    cookie = None
    for name in request.COOKIES.keys():
        if name.startswith('_shibsession_'):
            cookie = name + '=' + request.COOKIES[name]
    if cookie:
        return {
            'SHIB_LOGOUT_URL': '/Shibboleth.sso/Logout?%s' % cookie,
        }
    if request.user.is_authenticated:
        # Don't have a Shibboleth cookie, so must be a local login
        return {
            'SHIB_LOGOUT_URL': '/logout',
        }
    return {}
```

## Restart all services

Restart Apache, Shibboleth, and MDID to activate the changes:

```
service httpd start
service shibd start
supervisorctl restart mdid:mdid_app
```
