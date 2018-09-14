#!/usr/bin/env bash

echo Creating MDID Solr core

mkdir -p /opt/solr/data/mdid/conf /opt/solr/data/mdid/lang /opt/solr/data/mdid/data
touch /opt/solr/data/mdid/core.properties /opt/solr/data/mdid/protwords.txt /opt/solr/data/mdid/stopwords.txt /opt/solr/data/mdid/synonyms.txt
cp /opt/solr_install/solr/example/files/conf/lang/stopwords_en.txt /opt/solr/data/mdid/lang
cp /opt/mdid/rooibos/solr7/conf/* /opt/solr/data/mdid/conf
chown -R solr:solr /opt/solr/data/mdid
systemctl restart solr

su vagrant << END
source /opt/mdid/venv/bin/activate
pip install --upgrade -r /opt/mdid/rooibos/requirements.txt
export PYTHONPATH=/opt/mdid:/opt/mdid/rooibos
export DJANGO_SETTINGS_MODULE=rooibos_settings.vagrant
django-admin collectstatic --noinput
django-admin migrate --noinput
# run a second time because of foreign key constraints errors on initial run
django-admin migrate --noinput
END

su vagrant << ENDSU
cat > ~/.bash_aliases << END
export PYTHONPATH=/opt/mdid:/opt/mdid/rooibos
export DJANGO_SETTINGS_MODULE=rooibos_settings.vagrant
. /opt/mdid/venv/bin/activate
END
ENDSU
