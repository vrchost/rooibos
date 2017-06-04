#!/usr/bin/env bash

mkdir -p /opt/solr/mdid/conf
touch /opt/solr/mdid/core.properties
mkdir -p /opt/solr/mdid/data
cp /vagrant/solr4/template/conf/* /opt/solr/mdid/conf
chown -R jetty:jetty /opt/solr
service jetty8 restart

su ubuntu << END
cd /opt/mdid
source venv/bin/activate
pip install --upgrade -r /vagrant/requirements.txt
export PYTHONPATH=.
export DJANGO_SETTINGS_MODULE=rooibos_settings.vagrant
django-admin.py collectstatic --noinput
django-admin.py migrate --noinput
END
