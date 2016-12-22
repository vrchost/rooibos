#!/usr/bin/env bash

cat > /etc/supervisor/conf.d/mdid.conf << END
[group:mdid]
programs=mdid_app,celery,celery_solr,celery_beat

[program:mdid_app]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.vagrant"
command=/opt/mdid/venv/bin/gunicorn -t 60 -w 4 -b 127.0.0.1:8001 rooibos.wsgi:application
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/gunicorn.log

[program:celery]
directory=/opt/mdid/
environment=PYTHONPATH="/opt/mdid",DJANGO_SETTINGS_MODULE="rooibos_settings.vagrant",PATH="/opt/mdid/venv/bin"
command=/opt/mdid/venv/bin/celery -A rooibos worker -Q celery-default -l info -n worker@%%h
user=ubuntu
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery.log

[program:celery_solr]
directory=/opt/mdid/
environment=PATH="/opt/mdid/venv/bin",DJANGO_SETTINGS_MODULE="rooibos_settings.vagrant",PYTHONPATH="/opt/mdid"
command=/opt/mdid/venv/bin/celery -A rooibos worker -Q celery-default-solr -l info -n worker-solr@%%h
user=vagrant
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery-solr.log

[program:celery_beat]
directory=/opt/mdid/
environment=PATH="/opt/mdid/venv/bin",DJANGO_SETTINGS_MODULE="rooibos_settings.vagrant",PYTHONPATH="/opt/mdid"
command=/opt/mdid/venv/bin/celery -A rooibos beat -s /opt/mdid/celerybeat-schedule -l info
user=vagrant
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery-beat.log
END

supervisorctl reload
