# Installation on Ubuntu Linux

The following instructions are for Ubuntu Linux 14.04 LTS and 16.04 LTS, but
should work with minor changes on other distributions as well.

Unless noted otherwise, all commands should be run as `root`.
Lines starting with `§§` are continuations of the previous line.
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
Edit `/etc/default/jetty8`:
```
NO_START=0
JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64/jre"
JAVA_OPTIONS="-Dsolr.solr.home=/opt/solr -Xmx768m
§§ -Djava.awt.headless=true"
```
MDID currently requires Solr 4; you may have to adjust the exact version as available when running the following commands:
```
mkdir -p /opt/solr-install
cd /opt/solr-install
wget https://archive.apache.org/dist/lucene/solr/4.10.4/
§§solr-4.10.4.tgz
tar xf solr-4.10.4.tgz
cp solr-4.10.4/dist/solr-4.10.4.war \
    /usr/share/jetty8/webapps/solr.war
cp -R solr-4.10.4/example/solr /opt
chown -R jetty:jetty /opt/solr
wget http://www.slf4j.org/dist/slf4j-1.7.5.tar.gz
tar xzf slf4j-1.7.5.tar.gz
mv slf4j-1.7.5/* /usr/share/jetty8/lib/ext
service jetty8 restart
```
## Install MDID
### Create database
Create a new MySQL database or restore an existing database from a previous MDID3 installation.
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
The following assumes you have downloaded the package to /opt/mdid.

Run the following commands as the `mdid` user.
```
sudo -iu mdid
cd /opt/mdid
tar xzf rooibos-*.tar.gz
mv rooibos-v* rooibos
mkdir scratch storage log static
```
### Create virtual environment
```
sudo -iu mdid  # switch to mdid user
cd /opt/mdid
virtualenv venv
source venv/bin/activate
pip install --allow-external --upgrade \
    -r rooibos/requirements.txt
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
Create a new file `/etc/nginx/sites-available/mid` with the following content:
```
server {
    listen   0.0.0.0:80;
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
cd /opt/mdid/rooibos
source /opt/mdid/venv/bin/activate
export PYTHONPATH="/opt/mdid/rooibos"
export DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
python manage.py $@
```
Create a new file `/opt/mdid/crontab` with the following content:
```
*/5 * * * * /bin/bash /opt/mdid/wrapper.sh solr index >
§§/opt/mdid/log/cron.log 2>> /opt/mdid/log/cron-error.log
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
mkdir -p /opt/solr/mdid/conf
touch /opt/solr/mdid/core.properties
mkdir -p /opt/solr/mdid/data
cp /opt/mdid/rooibos/solr4/template/conf/* /opt/solr/mdid/conf
chown -R jetty:jetty /opt/solr
service jetty8 restart
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
programs=mdid_app,mdid_worker

[program:mdid_app]
directory=/opt/mdid/rooibos
environment=PATH="/opt/mdid/venv/bin",
§§ PYTHONPATH="/opt/mdid/rooibos/rooibos_settings",
§§ DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/gunicorn -w 4 -b 127.0.0.1:8001
§§ rooibos.wsgi:application
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/gunicorn.log

[program:mdid_worker]
directory=/opt/mdid/rooibos
environment=PATH="/opt/mdid/venv/bin",
§§ PYTHONPATH="/opt/mdid/rooibos/rooibos_settings",
§§ DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/python manage.py runworkers
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/workers.log
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
