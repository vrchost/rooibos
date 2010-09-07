#!/usr/bin/env python
import os
import sys

install_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(install_dir)
sys.path.append(os.path.join(install_dir, 'rooibos', 'contrib'))

from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
