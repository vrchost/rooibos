#!/usr/bin/env bash

su vagrant << END
cd /opt/mdid
source venv/bin/activate
pip install --allow-external --upgrade -r /vagrant/requirements.txt
export PYTHONPATH=.
export DJANGO_SETTINGS_MODULE=rooibos_settings.vagrant
django-admin.py collectstatic --noinput
django-admin.py migrate --noinput
END
