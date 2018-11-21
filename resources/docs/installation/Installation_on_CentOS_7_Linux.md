# Installation on CentOS 7 Linux

The following instructions are for CentOS 7, but
should work with minor changes on other distributions as well.

Unless noted otherwise, all commands should be run as `root`.

## Server Preparation
### Packages
```
yum update
yum --enablerepo=extras install epel-release
yum groupinstall 'Development Tools'
yum install python-pip libjpeg-devel \
    nginx mariadb-server mariadb-devel python-devel \
    memcached unixODBC-devel openldap-devel \
    rabbitmq-server supervisor \
    python-pillow-devel python-imaging \
    giflib-devel freetype-devel
pip install virtualenv
```

### Enable services
```
systemctl enable nginx
systemctl enable rabbitmq-server.service
systemctl start nginx
systemctl start rabbitmq-server.service
firewall-cmd --permanent --zone=public --add-service=http 
firewall-cmd --permanent --zone=public --add-service=https
firewall-cmd --reload
```

### Configure MariaDB
Edit `/etc/my.cnf` and add the following lines to the `[mysqld]` section:
```
open-files-limit = 10000
innodb_file_per_table = 1
lower_case_table_names = 1
character-set-server = utf8
collation-server = utf8_unicode_ci
```
Enable and start:
```
systemctl enable mariadb
systemctl start mariadb
```

### Build GFX
```
mkdir -p /opt/tools
cd /opt/tools
wget http://www.swftools.org/swftools-0.9.2.tar.gz
tar xzf swftools-0.9.2.tar.gz
cd swftools-0.9.2
```
The `configure` file needs to be patched:

```
patch -l configure <<'EOF'
7112,7113c7112,7113
<             if test -f "/usr/lib/python$v/site-packages/PIL/_imaging.so";then
<                 PYTHON_LIB2="$PYTHON_LIB /usr/lib/python$v/site-packages/PIL/_imaging.so"
---
>             if test -f "/usr/lib64/python$v/site-packages/_imaging.so";then
>                 PYTHON_LIB2="$PYTHON_LIB /usr/lib64/python$v/site-packages/_imaging.so"
7118c7118
<       PYTHON_INCLUDES="-I/usr/include/python$PY_VERSION"
---
>       PYTHON_INCLUDES="-I/usr/include/python$PY_VERSION -I/usr/include/python$PY_VERSION/Imaging"
7203c7203
< sys.stdout.write(distutils.sysconfig.get_python_lib(plat_specific=0,standard_lib=0))
---
> sys.stdout.write(distutils.sysconfig.get_python_lib(plat_specific=1,standard_lib=0))
EOF
```

```
./configure
make
```

### Install ffmpeg
```
rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm
yum install ffmpeg
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
systemctl start solr
```

## Install MDID
### Create database
Create a new MySQL database or restore an existing database from a previous MDID3 installation.
_Note: When migration from MDID2, create a new MySQL database at this point._
Adjust the database name, user name, and password as needed:
```
mysql -u root
create database mdid character set utf8;
grant all privileges on mdid.* to mdid@localhost identified by 'rooibos';
\q
```

### Create user account
```
useradd -m mdid
```

### Move MDID into place
```
mkdir -p /opt/mdid
chown mdid:mdid /opt/mdid
```
The following assumes you have downloaded the package to /opt/mdid.

Run the following commands as the `mdid` user.
```
sudo -iu mdid
cd /opt/mdid
tar xzf rooibos-*.tar.gz
mv rooibos-v* rooibos
mkdir scratch storage log rooibos/log static
```

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
cd /opt/mdid/rooibos/rooibos_settings
cp template.py local_settings.py
```
Edit `local_settings.py` and change settings as needed.

Make sure to change `SECRET_KEY` to a unique value and do not share it!

Also, if possible, change the asterisk in `ALLOWED_HOSTS` to your server
host name, if you know it, for example `['mdid.yourschool.edu']`.

Change `SOLR_URL` to `http://localhost:8080/solr/mdid`.

Run the following command to initialize static files:
```
sudo -iu mdid  # switch to mdid user
source /opt/mdid/venv/bin/activate
cd /opt/mdid/rooibos
export PYTHONPATH="/opt/mdid/rooibos"
export DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
python manage.py collectstatic
```

### Create or update database schema
```
sudo -iu mdid  # switch to mdid user
cd /opt/mdid/rooibos
source /opt/mdid/venv/bin/activate
export PYTHONPATH="/opt/mdid/rooibos"
export DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
# The following command may fail
# - if so, running it a second time should work
python manage.py syncdb --noinput
python manage.py migrate
```

### Configure nginx
Create a new file `/etc/nginx/conf.d/mdid.conf` with the following content:
```
server {
    listen   0.0.0.0:80 default_server;
    keepalive_timeout 70;

    access_log /opt/mdid/log/access.log;
    error_log /opt/mdid/log/error.log;

    location /static/ {
        alias /opt/mdid/rooibos/static/;
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
Edit the file `/etc/nginx/nginx.conf` and remove the existing 
`server { ... }` section.

Run `nginx -s reload`.

### Configure crontab
Create a new file `/opt/mdid/wrapper.sh` with the following content:
```
#!/bin/bash
set -x
cd /opt/mdid/rooibos
source /opt/mdid/venv/bin/activate
export PYTHONPATH="/opt/mdid/rooibos"
export DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
python manage.py $@
```
Create a new file `/opt/mdid/crontab` with the following content:
```
*/5 * * * * /bin/bash /opt/mdid/wrapper.sh solr index > /opt/mdid/log/cron.log 2>> /opt/mdid/log/cron-error.log
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
systemctl restart solr
```

### Install gfx
```
sudo -iu mdid  # switch to mdid user
cp /opt/tools/swftools-0.9.2/lib/python/*.so /opt/mdid/venv/lib/python2.7/site-packages/
```

### Configure supervisor
Create a new file `/etc/supervisord.d/mdid.ini` with the following content:
```
[group:mdid]
programs=mdid_app,celery,celery_solr,celery_beat

[program:mdid_app]
directory=/opt/mdid/rooibos
environment=PATH="/opt/mdid/venv/bin",PYTHONPATH="/opt/mdid/rooibos/rooibos_settings",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
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

Start supervisor and enable it to automatically start in the future:
```
systemctl start supervisord.service
systemctl enable supervisord.service
```

Load the configuration:
```
supervisorctl reload
```

## Further steps
In a production environment, the following topics should be investigated:
* Configure swap space
* SSL certificate for nginx
* Log rotation for log files in `/opt/mdid/log`
* Server and process monitoring
* Backup


## Note on SELinux

You may have to allow HTTP traffic for port 8001:

```
semanage port -a -t http_port_t -p tcp 8001
```
