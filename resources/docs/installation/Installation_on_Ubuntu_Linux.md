# Installation on Ubuntu Linux

The following instructions are for Ubuntu Linux 14.04 LTS and 16.04 LTS, but
should work with minor changes on other distributions as well.

Unless noted otherwise, all commands should be run as `root`.

## Server Preparation
### Packages
```
apt-get update
apt-get install python-pip libjpeg-dev libfreetype6-dev \
    nginx mysql-server-5.5 libmysqlclient-dev python-dev \
    libldap2-dev libsasl2-dev unixodbc-dev memcached \
    jetty8 rabbitmq-server supervisor
ln -s -f /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/
ln -s -f /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
ln -s -f /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/
pip install virtualenv
```
### Enable nginx
```
rm -f /etc/nginx/sites-enabled/default
update-rc.d nginx enable
service nginx start
```
### Configure MySQL
Edit `/etc/mysql/my.cnf` and add the following lines to the `[mysqld]` section:
```
open-files-limit = 10000
innodb_file_per_table = 1
lower_case_table_names = 1
character-set-server = utf8
collation-server = utf8_unicode_ci
```
Reload the new configuration:
```
service mysql restart
```
### Build GFX
```
mkdir -p /opt/tools
cd /opt/tools
wget http://www.swftools.org/swftools-0.9.2.tar.gz
tar xzf swftools-0.9.2.tar.gz
cd swftools-0.9.2
./configure
make
```
### Build ffmpeg
```
apt-get install autoconf automake build-essential \
    libass-dev libfreetype6-dev libtheora-dev libtool \
    libvorbis-dev pkg-config texinfo zlib1g-dev yasm \
    libx264-dev libmp3lame-dev
mkdir -p /opt/ffmpeg
cd /opt/ffmpeg
wget http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
tar xjf ffmpeg-snapshot.tar.bz2
cd ffmpeg
PATH="/opt/ffmpeg/bin:$PATH" \
    PKG_CONFIG_PATH="/opt/ffmpeg/lib/pkgconfig" \
    ./configure \
    --prefix="/opt/ffmpeg" \
    --pkg-config-flags="--static" \
    --extra-cflags="-I/opt/ffmpeg/include" \
    --extra-ldflags="-L/opt/ffmpeg/lib" \
    --bindir="/opt/ffmpeg/bin" \
    --enable-gpl \
    --enable-libass \
    --enable-libfreetype \
    --enable-libmp3lame \
    --enable-libtheora \
    --enable-libvorbis \
    --enable-libx264
PATH="/opt/ffmpeg/bin:$PATH" make install
cp /opt/ffmpeg/bin/* /usr/local/bin
```
### Install Solr
MDID currently requires Solr 7; you may have to adjust the exact version as
available when running the following commands:
```
mkdir -p /opt/solr_install /opt/solr
cd /opt/solr_install
wget https://archive.apache.org/dist/lucene/solr/7.3.1/solr-7.3.1.tgz
tar xzf solr-7.3.1.tgz solr-7.3.1/bin/install_solr_service.sh --strip-components=2
./install_solr_service.sh solr-7.3.1.tgz -f -d /opt/solr -i /opt/solr_install -n
sed -i -E 's/#SOLR_HEAP="512m"/SOLR_HEAP="2048m"/' /etc/default/solr.in.sh
service solr start
```

## Install MDID
### Create database
Create a new MySQL database or restore an existing database from a previous
MDID3 installation.

_Note: When migration from MDID2, create a new MySQL database at this point._

Adjust the database name, user name, and password as needed:
```
mysql -u root
create database mdid character set utf8;
grant all privileges on mdid.* to mdid@localhost
    identified by 'rooibos';
\q
```
### Create user account
```
adduser --disabled-password mdid
```
### Move MDID into place
```
mkdir -p /opt/mdid
chown mdid:mdid /opt/mdid
```

Run the following commands as the `mdid` user.
```
sudo -iu mdid
cd /opt/mdid
mkdir scratch storage log static
```

Extract the package so that the contents are placed in `/opt/mdid/rooibos`:

    /opt/mdid/rooibos/requirements.txt
    /opt/mdid/rooibos/rooibos
    /opt/mdid/rooibos/rooibos_settings
    ...

This way, updated packages can be installed by just replacing
`/opt/mdid/rooibos` with the new version.

### Create virtual environment
```
sudo -iu mdid  # switch to mdid user
cd /opt/mdid
virtualenv venv
source venv/bin/activate
pip install --allow-external --upgrade -r rooibos/requirements.txt
```
### Configure MDID
```
sudo -iu mdid  # switch to mdid user
cd /opt/mdid
cp -r rooibos/rooibos_settings rooibos_settings
cd /opt/mdid/rooibos_settings
cp template.py local_settings.py
```
Edit `local_settings.py` and change settings as needed, including:

```
SOLR_URL = 'http://localhost:8983/solr/mdid'
```

Make sure to change `SECRET_KEY` to a unique value and do not share it!

Also, if possible, change the asterisk in `ALLOWED_HOSTS` to your server
host name, if you know it, for example `['mdid.yourschool.edu']`.

Run the following command to initialize static files:
```
sudo -iu mdid  # switch to mdid user
source /opt/mdid/venv/bin/activate
export PYTHONPATH="/opt/mdid:/opt/mdid/rooibos"
export DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
django-admin collectstatic
```
### Create or update database schema
```
sudo -iu mdid  # switch to mdid user
source /opt/mdid/venv/bin/activate
export PYTHONPATH="/opt/mdid:/opt/mdid/rooibos"
export DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
# The following command may fail
# - if so, running it a second time should work
django-admin syncdb --noinput
django-admin migrate
```
### Configure nginx
Create a new file `/etc/nginx/sites-available/mdid` with the following content:
```
server {
    listen   0.0.0.0:80;
    keepalive_timeout 70;

    access_log /opt/mdid/log/access.log;
    error_log /opt/mdid/log/error.log;

    location /static/ {
        alias /opt/mdid/static/;
        expires 30d;
    }

    location / {
        proxy_set_header X-Real-IP  $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host $host;
        proxy_pass http://127.0.0.1:8001;
    }
    client_max_body_size 50M;
}
```
Activate the site:
```
cd /etc/nginx/sites-enabled
ln -s -f ../sites-available/mdid mdid
```
### Configure crontab
Create a new file `/opt/mdid/wrapper.sh` with the following content:
```
#!/bin/bash
set -x
source /opt/mdid/venv/bin/activate
export PYTHONPATH="/opt/mdid/rooibos"
export DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
django-admin $@
```
Create a new file `/opt/mdid/crontab` with the following content:
```
0 * * * * /bin/bash /opt/mdid/wrapper.sh runjobs hourly
0 4 * * * /bin/bash /opt/mdid/wrapper.sh runjobs daily
0 5 * * 0 /bin/bash /opt/mdid/wrapper.sh runjobs weekly
0 6 1 * * /bin/bash /opt/mdid/wrapper.sh runjobs monthly
0 7 1 1 * /bin/bash /opt/mdid/wrapper.sh runjobs yearly
```
Activate the file:
```
sudo -iu mdid  # switch to mdid user
crontab /opt/mdid/crontab
```
### Configure solr
```
mkdir -p /opt/solr/data/mdid/conf \
    /opt/solr/data/mdid/lang \
    /opt/solr/data/mdid/data
touch /opt/solr/data/mdid/core.properties \
    /opt/solr/data/mdid/protwords.txt \
    /opt/solr/data/mdid/stopwords.txt \
    /opt/solr/data/mdid/synonyms.txt
cp /opt/solr_install/solr/example/files/conf/lang/stopwords_en.txt \
    /opt/solr/data/mdid/lang
cp /opt/mdid/solr7/conf/* \
    /opt/solr/data/mdid/conf
chown -R solr:solr /opt/solr/data/mdid
service solr restart
```
### Install gfx
```
sudo -iu mdid  # switch to mdid user
cp /opt/tools/swftools-0.9.2/lib/python/*.so \
    /opt/mdid/venv/lib/python2.7/site-packages/
```
### Configure supervisor
Create a new file `/etc/supervisor/conf.d/mdid.conf` with the following content:
```
[group:mdid]
programs=mdid_app,celery,celery_solr,celery_beat

[program:mdid_app]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/gunicorn -w 4 -b 127.0.0.1:8001 rooibos.wsgi:application
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/gunicorn.log

[program:celery]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/celery -A rooibos worker -Q celery-default -l info -n worker@localhost
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery.log

[program:celery_solr]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/celery -A rooibos worker -Q celery-default-solr -l info -n worker-solr@localhost
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery-solr.log

[program:celery_beat]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/celery -A rooibos beat -s /opt/mdid/celerybeat-schedule -l info --pidfile=/tmp/celerybeat.pid
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery-beat.log
```
Load the configuration:
```
supervisorctl reload
```
## Further steps
In a production environment, the following topics should be investigated:
* Configure swap space
* Firewall
MDID only requires port 80 to be open (port 443 if SSL is configured)
* SSL certificate for nginx
* Log rotation for log files in `/opt/mdid/log`
* Server and process monitoring
* Backup

## Shibboleth support

To use Shibboleth for user authentication, follow the steps below to
modify your working MDID installation to connect to your IdP.

### Install additional packages

apt-get install apache2 apache2-utils libapache2-mod-shib2 libshibsp-dev \
    libshibsp-doc opensaml2-tools shibboleth-sp2-schemas

### Configure Shibboleth

Configure your Shibboleth SP in `/etc/shibboleth/shibboleth2.xml`, including
setting the application ID to `mdid`.

Make sure to add a key or generate a new key using `shib-keygen`.

Uncomment the attributes you want to use in `attribute-map.xml`.

### Configure apache

Modify `/etc/apache2/ports.conf` and change all instances of port 80 to
port 8100.

Enable apache modules:
```
a2enmod rewrite
a2enmod proxy
a2enmod proxy_http
a2enmod headers
ln -s -f /etc/apache2/mods-available/shib2.load \
    /etc/apache2/mods-enabled/shib2.load
apachectl restart
```
Add a new apache site configuration file at
`/etc/apache2/sites-available/mdid.conf`, replacing `your.server.domain` with
the appropriate value:
```
<VirtualHost 127.0.0.1:8100>
        UseCanonicalName Off

        ServerName https://your.server.domain

        DocumentRoot /home/mdid/www

        <Directory /home/mdid/www>
            Order allow,deny
            Allow from all
            Require all granted
        </Directory>

        Alias /static/ "/opt/instances/mdid/static/"

        ErrorLog /opt/instances/%(instance)s/log/apache2-error.log
        CustomLog /opt/instances/mdid/log/apache2-access.log combined

        <Location /shibboleth>
                AuthType shibboleth
                ShibRequireSession On
                ShibUseHeaders On
                ShibRequestSetting applicationId mdid
                require valid-user
        </Location>

        ProxyPreserveHost On
        <Location />
            ProxyPass http://127.0.0.1:8001/
            ProxyPassReverse http://127.0.0.1:8001/
            RequestHeader set X-FORWARDED-PROTOCOL ssl
            RequestHeader set X-FORWARDED-SSL on
            RequestHeader set Host your.server.domain
        </Location>

        <Location /Shibboleth.sso>
                SetHandler shib
                ShibRequestSetting applicationId mdid
                ProxyPass "!"
        </Location>
</VirtualHost>
```
Activate the file:
```
ln -s -f /etc/apache2/sites-available/mdid.conf \
    /etc/apache2/sites-enabled/999-mdid.conf
```

### Configure nginx

In your nginx site file `/etc/nginx/sites-available/mdid`, change the port
number in the `proxy_pass` statement from 8001 to 8100.

### Configure MDID

Add the following settings to your MDID configuration, changing attribute
names as required:

```
SHIB_ENABLED = True
SHIB_ATTRIBUTE_MAP = {
    "HTTP_MAIL": (True, "mail"),
    "HTTP_GIVENNAME": (False, "givenName"),
    "HTTP_SN": (False, "sn"),
    "HTTP_USERNAME": (True, "username"),
}
SHIB_USERNAME = "username"
SHIB_EMAIL = "mail"
SHIB_FIRST_NAME = "givenName"
SHIB_LAST_NAME = "sn"
```

By default MDID will not show a logout link, but if your Shibboleth setup
allows logouts, you can configure the logout URL with

```
SHIB_LOGOUT_URL = "http://link.to.your.shibboleth.logout"
```

### Restart all services

```
service shibd restart
apache2ctl graceful
nginx -s reload
supervisorctl restart mdid:*
```
