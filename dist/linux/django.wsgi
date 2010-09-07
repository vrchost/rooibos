import os
import sys

sys.path.append('/var/local/mdid')
sys.path.append('/var/local/mdid/rooibos/contrib')

os.environ['DJANGO_SETTINGS_MODULE'] = 'rooibos.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
