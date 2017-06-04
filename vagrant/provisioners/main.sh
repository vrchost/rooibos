#!/usr/bin/env bash

debconf-set-selections <<< 'mysql-server mysql-server/root_password password changeme'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password changeme'

apt-get update
apt-get install -y python-pip libjpeg-dev libfreetype6-dev \
    nginx mysql-server libmysqlclient-dev python-dev \
    libldap2-dev libsasl2-dev unixodbc-dev memcached \
    jetty8 rabbitmq-server supervisor
ln -s -f /usr/lib/x86_64-linux-gnu/libjpeg.so /usr/lib/
ln -s -f /usr/lib/x86_64-linux-gnu/libz.so /usr/lib/
ln -s -f /usr/lib/x86_64-linux-gnu/libfreetype.so /usr/lib/
pip install --upgrade pip
pip install virtualenv

rm -f /etc/nginx/sites-enabled/default
update-rc.d nginx enable
service nginx start

if [ ! -e /usr/local/bin/ffmpeg ] ; then
    apt-get install -y autoconf automake build-essential \
        libass-dev libfreetype6-dev libtheora-dev libtool \
        libvorbis-dev pkg-config texinfo zlib1g-dev yasm \
        libx264-dev libmp3lame-dev
    mkdir -p /tmp/ffmpeg
    cd /tmp/ffmpeg
    rm -rf ffmpeg
    wget -nv http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
    tar xjf ffmpeg-snapshot.tar.bz2
    cd ffmpeg
    PATH="/tmp/ffmpeg/bin:$PATH" \
        PKG_CONFIG_PATH="/tmp/ffmpeg/lib/pkgconfig" \
        ./configure \
        --prefix="/tmp/ffmpeg" \
        --pkg-config-flags="--static" \
        --extra-cflags="-I/tmp/ffmpeg/include" \
        --extra-ldflags="-L/tmp/ffmpeg/lib" \
        --bindir="/tmp/ffmpeg/bin" \
        --enable-gpl \
        --enable-libass \
        --enable-libfreetype \
        --enable-libmp3lame \
        --enable-libtheora \
        --enable-libvorbis \
        --enable-libx264
    PATH="/tmp/ffmpeg/bin:$PATH" make install
    cp /tmp/ffmpeg/bin/* /usr/local/bin
fi

cat > /etc/default/jetty8 << END
NO_START=0
VERBOSE=yes
JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64/jre"
JAVA_OPTIONS="-Dsolr.solr.home=/opt/solr -Xmx768m -Djava.awt.headless=true -Djava.net.preferIPv4Stack=true"
END

if [ ! -e /usr/share/jetty8/webapps/solr.war ] ; then
    mkdir -p /tmp/solr-install
    cd /tmp/solr-install
    wget -nv https://archive.apache.org/dist/lucene/solr/4.10.4/solr-4.10.4.tgz
    tar xf solr-4.10.4.tgz
    cp solr-4.10.4/dist/solr-4.10.4.war /usr/share/jetty8/webapps/solr.war
    cp -R solr-4.10.4/example/solr /opt
    chown -R jetty:jetty /opt/solr
    wget -nv http://www.slf4j.org/dist/slf4j-1.7.5.tar.gz
    tar xzf slf4j-1.7.5.tar.gz
    mv slf4j-1.7.5/* /usr/share/jetty8/lib/ext
    service jetty8 restart
fi

mkdir -p /opt/mdid/scratch /opt/mdid/storage /opt/mdid/log /opt/mdid/static
chown -R ubuntu:ubuntu /opt/mdid
if [ ! -e /opt/mdid/venv ] ; then
    cd /opt/mdid
    sudo -u ubuntu virtualenv venv
fi

if [ ! -e /opt/mdid/venv/lib/python2.7/site-packages/gfx.so ] ; then
    cd /tmp
    wget -nv http://www.swftools.org/swftools-0.9.2.tar.gz
    tar xzf swftools-0.9.2.tar.gz
    cd swftools-0.9.2
    ./configure
    make
    sudo -u ubuntu cp lib/python/gfx.so /opt/mdid/venv/lib/python2.7/site-packages/
fi

cat > /etc/nginx/sites-enabled/mdid << END
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

ln -s -f -n /vagrant/rooibos /opt/mdid/rooibos
ln -s -f -n /vagrant/rooibos_settings /opt/mdid/rooibos_settings

mysql -u root --password=changeme << END
create database if not exists mdid character set utf8;
grant all privileges on mdid.* to mdid@localhost identified by 'mdid';
END
