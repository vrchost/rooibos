# Upgrading from MDID 3.3.x

To upgrade an installation of MDID 3.3 or later, replace the old
package folder with the new package, keeping your `rooibos_settings` and
any other custom files and folders in place.  Make sure to copy the new
`rooibos_settings/base.py`, since it likely includes changes.

Afterwards, run the following commands to apply any database changes.

```
django-admin migrate storage --fake-initial --noinput
django-admin migrate --noinput
```

In your `local_settings.py`, change or add the following setting to reflect
the new port used by Solr:

```
SOLR_URL = 'http://localhost:8983/solr/mdid'
```

# Upgrading from MDID 3.2.x

To upgrade an installation of MDID 3.2.x, replace the old
package folder with the new package.  There may be new configuration settings,
so you will also need the new `rooibos_settings` folder, but bringing over 
your previous `local_settings.py` file and any other custom files and folders.

## Update virtual environment
```
sudo -iu mdid  # switch to mdid user
cd /opt/mdid
virtualenv venv
source venv/bin/activate
pip install --allow-external --upgrade -r rooibos/requirements.txt
```

## Upgrade solr

Follow the "Install Solr" and "Configure solr" sections in the installation
instructions for your distribution

In your `local_settings.py`, change or add the following setting to reflect
the new port used by Solr:

```
SOLR_URL = 'http://localhost:8983/solr/mdid'
```


## Migrate database

Run `django-admin migrate` to apply any database changes.

## Update supervisor configuration

### Ubuntu

Edit the file `/etc/supervisor/conf.d/mdid.conf` and completely remove the
`[program:mdid_worker]` section.

Change the `[group:mdid]` section to
```
programs=mdid_app,celery,celery_solr,celery_beat
```

Add the following sections at the end of the file:

```
[program:celery]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/celery -A rooibos worker -Q celery-default -l info -n worker@localhost
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery.log

[program:celery_solr]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/celery -A rooibos worker -Q celery-default-solr -l info -n worker-solr@localhost
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery-solr.log

[program:celery_beat]
environment=PYTHONPATH="/opt/mdid:/opt/mdid/rooibos",DJANGO_SETTINGS_MODULE="rooibos_settings.local_settings"
command=/opt/mdid/venv/bin/celery -A rooibos beat -s /opt/mdid/celerybeat-schedule -l info --pidfile=/tmp/celerybeat.pid
user=mdid
autostart=true
autorestart=true
stopasgroup=true
redirect_stderr=true
stdout_logfile=/opt/mdid/log/celery-beat.log
```

Load the configuration:
```
supervisorctl reload
```

### CentOS

Follow the Ubuntu instructions above, but the supervisor configuration
file is located at `/etc/supervisord.d/mdid.ini`.


# Upgrading from MDID 3.0 or 3.1

Perform a new installation pointing to your existing database and image files.

Afterwards, run

    django-admin migrate --fake-initial
    django-admin migrate

If you receive an error

    Unknown column 'data_collection.order' in 'field list'

run this command against your MySQL database from within the MySQL shell:

    ALTER TABLE data_collection ADD COLUMN `order` INT NULL DEFAULT 0;

If you receive an error

    Error creating new content types

run this command against your MySQL database from within the MySQL shell:

    ALTER TABLE django_content_type DROP COLUMN name


# Upgrading from MDID2

* Perform a new installation with a blank database.
* Copy the `config.xml` file from your MDID2 installation to a place accessible
  from the new installation.
* If necessary, adjust the `<database>` section in the `config.xml` file so
  that it can be used to connect to the database from the new installation.
* Run `django-admin mdid2migrate path/to/config.xml`
* Copy the full-size images from the MDID2 installation to a place accessible
  to the new installation.
* In MDID3, under Management>Manage Storages, fix the paths to the different
  storage directories.
* Run a full re-index with `django-admin solr reindex`.
