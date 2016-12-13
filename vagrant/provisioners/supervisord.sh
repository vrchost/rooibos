#!/usr/bin/env bash

cat > /etc/supervisor/conf.d/mdid.conf << END
[group:mdid]
programs=mdid_app,mdid_worker

[program:mdid_app]
directory=/opt/mdid/rooibos
environment=PATH="/opt/mdid/venv/bin",DJANGO_SETTINGS_MODULE="rooibos_settings.vagrant",PYTHONPATH="/opt/mdid"
command=/opt/mdid/venv/bin/gunicorn -w 4 -b 127.0.0.1:8001 rooibos.wsgi:application
user=vagrant
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/gunicorn.log

[program:mdid_worker]
directory=/opt/mdid/rooibos
environment=PATH="/opt/mdid/venv/bin",DJANGO_SETTINGS_MODULE="rooibos_settings.vagrant",PYTHONPATH="/opt/mdid"
command=/opt/mdid/venv/bin/django-admin.py runworkers
user=vagrant
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/workers.log
END

supervisorctl reload
