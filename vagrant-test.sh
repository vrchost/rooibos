#!/bin/bash
PYTHONPATH=/vagrant DJANGO_SETTINGS_MODULE=rooibos_settings.test django-admin test -t /vagrant $*
