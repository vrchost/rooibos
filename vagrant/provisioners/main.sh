#!/usr/bin/env bash

debconf-set-selections <<< 'mysql-server mysql-server/root_password password changeme'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password changeme'

apt-get update
apt-get install -y python python-pip libjpeg-dev libfreetype6-dev \
    nginx mysql-server libmysqlclient-dev python-dev \
    libldap2-dev libsasl2-dev unixodbc-dev memcached \
    rabbitmq-server supervisor ffmpeg openjdk-11-jre-headless \
    python-virtualenv
ln -s -f /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/
ln -s -f /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
ln -s -f /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/

rm -f /etc/nginx/sites-enabled/default
update-rc.d nginx enable
service nginx start

if [ ! -e /etc/default/solr.in.sh ] ; then
    SOLR_VERSION=7.4.0
    id -u solr &>/dev/null || echo -e '\\n\\n\\n\\n\\n\\n' | adduser --disabled-password solr
    mkdir -p /opt/solr_install /opt/solr
    chown solr:solr /opt/solr
    cd /vagrant/temp
    [ -e solr-$SOLR_VERSION.tgz ] || wget https://archive.apache.org/dist/lucene/solr/$SOLR_VERSION/solr-$SOLR_VERSION.tgz
    cd /opt/solr_install
    tar xzf /vagrant/temp/solr-$SOLR_VERSION.tgz solr-$SOLR_VERSION/bin/install_solr_service.sh --strip-components=2
    ./install_solr_service.sh /vagrant/temp/solr-$SOLR_VERSION.tgz -f -d /opt/solr -i /opt/solr_install -n
    service solr start
fi

cat > /etc/nginx/sites-available/mdid << END
server {
    listen   0.0.0.0:8800;
    keepalive_timeout 70;

    access_log /opt/mdid/log/access.log;
    error_log /opt/mdid/log/error.log;

    location /static/ {
        alias /opt/mdid/static/;
        expires 30d;
    }

    location / {
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Forwarded-Host \$host:8800;
        proxy_set_header Host \$host;
        proxy_pass http://127.0.0.1:8001;
    }
    client_max_body_size 50M;
}
END
ln -s -f /etc/nginx/sites-available/mdid /etc/nginx/sites-enabled/mdid
rm -f /etc/nginx/sites-enabled/default
nginx -s reload

mysql -u root --password=changeme << END
create database if not exists mdid character set utf8;
grant all privileges on mdid.* to mdid@localhost identified by 'mdid';
END



mkdir -p /opt/mdid/scratch /opt/mdid/storage /opt/mdid/log /opt/mdid/static
ln -s -f -n /vagrant /opt/mdid/rooibos
ln -s -f -n /vagrant/rooibos_settings /opt/mdid/rooibos_settings

chown -R vagrant:vagrant /opt/mdid
if [ ! -e /opt/mdid/venv ] ; then
    cd /opt/mdid
    sudo -u vagrant virtualenv venv
fi

if [ ! -e /opt/mdid/venv/lib/python2.7/site-packages/gfx.so ] ; then
    cd /vagrant/temp
    if [ ! -e swftools-0.9.2.tar.gz ] ; then
        wget -q http://www.swftools.org/swftools-0.9.2.tar.gz
        tar xzf swftools-0.9.2.tar.gz
    fi
    cd swftools-0.9.2
    if [ ! -e lib/python/gfx.so ] ; then
        ./configure > /dev/null
        make > /dev/null
    fi
    sudo -u vagrant cp lib/python/gfx.so /opt/mdid/venv/lib/python2.7/site-packages/
fi
