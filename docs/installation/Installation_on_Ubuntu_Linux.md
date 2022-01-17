# Installation on Ubuntu Linux

The following instructions are for Ubuntu Linux 20.04 LTS, but
should work with minor changes on other distributions as well.

Unless noted otherwise, all commands should be run as `root`.

## Server Preparation
### Packages
```
apt-get update
apt-get install -y python3 python3-pip libjpeg-dev libfreetype6-dev \
    nginx mysql-server libmysqlclient-dev python3-dev \
    libldap2-dev libsasl2-dev unixodbc-dev memcached \
    rabbitmq-server supervisor ffmpeg openjdk-11-jre-headless \
    python3-virtualenv libssl-dev poppler-utils
```
### Enable nginx
```
rm -f /etc/nginx/sites-enabled/default
update-rc.d nginx enable
service nginx start
```
### Create user account
```
adduser --disabled-password mdid
mkdir -p /opt/mdid
chown mdid:mdid /opt/mdid
```
### Create virtual environment
```
sudo -iu mdid  # switch to mdid user
cd /opt/mdid  # or another directory of your choice
python3 -m virtualenv -p python3 venv
source venv/bin/activate
pip install mdid
# or to install test version:
# pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple mdid
mdid init
```
### Install Solr
MDID currently requires Solr 8; you may have to adjust the exact version as
available when running the following commands.
Please note that you want to use at least version 8.11.1 of Solr to avoid the Log4j vulnerability.
```
mkdir -p /opt/solr_install /opt/solr
cd /opt/solr_install
wget https://archive.apache.org/dist/lucene/solr/8.11.1/solr-8.11.1.tgz
tar xzf solr-8.11.1.tgz solr-8.11.1/bin/install_solr_service.sh --strip-components=2
./install_solr_service.sh solr-8.11.1.tgz -f -d /opt/solr -i /opt/solr_install -n
sed -i -E 's/#SOLR_HEAP="512m"/SOLR_HEAP="2048m"/' /etc/default/solr.in.sh
ln -s /opt/mdid/var/solr /opt/solr/data/mdid
chown -R solr:solr /opt/solr/data/mdid/
service solr start
```
### Configure MySQL
```
ln -s /opt/mdid/service-config/mysql /etc/mysql/mysql.conf.d/mdid.cnf
service mysql restart
```
### Create database
Create a new MySQL database or restore an existing database from a previous
MDID3 installation. Adjust the database name, user name, and password as needed:
```
mysql -u root
create database mdid character set utf8;
create user mdid@localhost identified by 'rooibos';
grant all privileges on mdid.* to mdid@localhost;
\q
```
### Configure MDID
Edit `/opt/mdid/config/settings.py` and change the database and other settings 
as needed. 

Also, if possible, change the asterisk in `ALLOWED_HOSTS` to your server
host name, if you know it, for example `['mdid.yourschool.edu']`.

Run the following command to initialize static files and migrate the database
to the latest version:
```
sudo -iu mdid  # switch to mdid user
source /opt/mdid/venv/bin/activate
mdid collectstatic
mdid migrate
```
### Configure nginx
```
ln -s /opt/mdid/service-config/nginx /etc/nginx/sites-enabled/mdid
```
Place your server SSL certificate files named `server.key` and `server.crt`
in `/opt/mdid/ssl`, or generate some sample self-signed certificates for
temporary use:
```
openssl genrsa -out /opt/mdid/ssl/server.key
openssl req -new -key /opt/mdid/ssl/server.key -out /opt/mdid/ssl/server.csr
openssl x509 -req -days 365 -in /opt/mdid/ssl/server.csr -signkey /opt/mdid/ssl/server.key -out /opt/mdid/ssl/server.crt
```
### Configure crontab
```
sudo -iu mdid  # switch to mdid user
crontab /opt/mdid/service-config/crontab
```
### Configure supervisor
Create a new file `/etc/supervisor/conf.d/mdid.conf` with the following content:
```
ln -s /opt/mdid/service-config/supervisor /etc/supervisor/conf.d/mdid.conf
supervisorctl reload
```

## Shibboleth support

To use Shibboleth for user authentication, follow the steps below to
modify your working MDID installation to connect to your IdP.

### Install additional packages
```
apt-get install apache2 apache2-utils libapache2-mod-shib2 libshibsp-dev \
    libshibsp-doc opensaml2-tools shibboleth-sp2-schemas
```
### Configure Shibboleth

Configure your Shibboleth SP in `/etc/shibboleth/shibboleth2.xml`, including
setting the application ID to `mdid`.

Make sure to add a key or generate a new key using `shib-keygen`.

Uncomment the attributes you want to use in `attribute-map.xml`.

### Configure apache

Modify `/etc/apache2/ports.conf` and change all instances of port 80 to
port 8100.

Enable apache modules and configure site:
```
a2enmod rewrite
a2enmod proxy
a2enmod proxy_http
a2enmod headers
ln -s -f /etc/apache2/mods-available/shib2.load /etc/apache2/mods-enabled/shib2.load
ln -s /opt/mdid/service-config/apache /etc/apache2/sites-enabled/999-mdid.conf
apachectl restart
```

### Configure nginx

In your nginx site file `/opt/mdid/service-config/nginx`, change the port
number in the `proxy_pass` statement from 8001 to 8100.

### Configure MDID

Add the following settings to your MDID configuration file at
`/opt/mdid/config/settings.py`, changing attribute names as required:

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
