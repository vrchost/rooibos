import os
import random
import string
import sys
from django.core.management import execute_from_command_line


DIRECTORIES = 'scratch storage log static templates config'.split()

CONFIG = """
import os
from rooibos.settings.base import *

install_dir = '%(install_dir)s'

SECRET_KEY = '%(secret_key)s'

LOG_DIR = os.path.join(install_dir, 'log')
STATIC_ROOT = os.path.join(install_dir, 'static')
SCRATCH_DIR = os.path.join(install_dir, 'scratch')
TEMPLATES[0]['DIRS'].append(os.path.join(install_dir, 'templates'))

# Add the hostname of your server, or keep '*' to allow all host names
ALLOWED_HOSTS = ['*']

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mdid',
        'USER': 'mdid',
        'PASSWORD': 'rooibos',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
            'use_unicode': True,
            'charset': 'utf8',
        },
    }
}
"""


def init():
    """Initializes an MDID instance in the current directory"""
    print("Initializing")
    for directory in DIRECTORIES:
        os.makedirs(directory, exist_ok=True)
    defaults = dict(
        secret_key = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(64)
        ),
        install_dir = os.path.abspath('.'),
    )
    settings_file = os.path.join('config', 'settings.py')
    if os.path.exists(settings_file):
        settings_file += '.template'
    with open(settings_file, 'w') as output:
        output.write(CONFIG % defaults)
    with open(os.path.join('config', '__init__.py'), 'w') as output:
        pass


def main():
    """Run MDID and Django admin commands"""
    python_path = os.getenv('PYTHONPATH')
    if not python_path:
        os.putenv('PYTHONPATH', '.')
        sys.path.append('.')

    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init()
        sys.exit(0)

    settings_module = os.getenv('DJANGO_SETTINGS_MODULE')
    if not settings_module:
        try:
            import config.settings
            os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
        except ImportError:
            print('Could not find MDID settings, have you run "mdid init"?')
    # sys.argv = ['django-admin'] + sys.argv[1:]
    sys.exit(execute_from_command_line())
