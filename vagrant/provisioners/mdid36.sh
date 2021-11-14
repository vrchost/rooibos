#!/usr/bin/env bash

set -x

debconf-set-selections <<< 'mysql-server mysql-server/root_password password changeme'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password changeme'

apt-get update
apt-get install -y python3 python3-pip libjpeg-dev libfreetype6-dev \
    nginx mysql-server libmysqlclient-dev python3-dev \
    libldap2-dev libsasl2-dev unixodbc-dev memcached \
    rabbitmq-server supervisor ffmpeg openjdk-11-jre-headless \
    python3-virtualenv libssl-dev poppler-utils

rm -f /etc/nginx/sites-enabled/default
update-rc.d nginx enable
service nginx start

mkdir -p /opt/mdid
chown vagrant:vagrant /opt/mdid

ln -f -s /opt/mdid/service-config/mysql /etc/mysql/mysql.conf.d/mdid.cnf
service mysql restart

mysql -u root --password=changeme << END
create database if not exists mdid character set utf8;
create user if not exists mdid@localhost identified by 'rooibos';
grant all privileges on mdid.* to mdid@localhost;
END

sudo -u vagrant -s -- <<EOF
  cd /opt/mdid  # or another directory of your choice
  [ -d venv ] || python3 -m virtualenv -p python3 venv
  source venv/bin/activate

  cd /vagrant
  python setup.py install

  cd /opt/mdid
  mdid init
  mdid collectstatic --noinput
  mdid migrate --noinput
EOF

[ -d /opt/solr ] || (
  mkdir -p /opt/solr_install /opt/solr
  cd /opt/solr_install
  wget https://archive.apache.org/dist/lucene/solr/7.7.3/solr-7.7.3.tgz
  tar xzf solr-7.7.3.tgz solr-7.7.3/bin/install_solr_service.sh --strip-components=2
  ./install_solr_service.sh solr-7.7.3.tgz -f -d /opt/solr -i /opt/solr_install -n
  sed -i -E 's/#SOLR_HEAP="512m"/SOLR_HEAP="2048m"/' /etc/default/solr.in.sh
  ln -s /opt/mdid/var/solr /opt/solr/data/mdid
  chown -R solr:solr /opt/solr/data/mdid/
)
service solr start

ln -f -s /opt/mdid/service-config/nginx /etc/nginx/sites-enabled/mdid

[ -f /opt/mdid/ssl/server.key ] || (
  openssl genrsa -out /opt/mdid/ssl/server.key
  openssl req -new -key /opt/mdid/ssl/server.key -out /opt/mdid/ssl/server.csr -subj "/C=US/ST=Example State/L=Example Location/O=Example Organization/OU=Example Department/CN=example.com"
  openssl x509 -req -days 365 -in /opt/mdid/ssl/server.csr -signkey /opt/mdid/ssl/server.key -out /opt/mdid/ssl/server.crt
)

ln -f -s /opt/mdid/service-config/supervisor /etc/supervisor/conf.d/mdid.conf
supervisorctl reload
