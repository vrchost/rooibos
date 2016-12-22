#!/usr/bin/env bash

mkdir -p /opt/solr/mdid/conf
touch /opt/solr/mdid/core.properties
mkdir -p /opt/solr/mdid/data
cp /vagrant/solr4/template/conf/* /opt/solr/mdid/conf
chown -R jetty:jetty /opt/solr
service jetty8 restart

su ubuntu << END
source /opt/mdid/venv/bin/activate
pip install --upgrade -r /opt/mdid/rooibos/requirements.txt
export PYTHONPATH=/opt/mdid:/opt/mdid/rooibos
export DJANGO_SETTINGS_MODULE=rooibos_settings.vagrant
django-admin collectstatic --noinput
django-admin migrate --noinput
END

su vagrant << ENDSU
cat > ~/.bash_aliases << END
export PYTHONPATH=/opt/mdid
export DJANGO_SETTINGS_MODULE=rooibos_settings.vagrant
. /opt/mdid/venv/bin/activate
END
ENDSU
