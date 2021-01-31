import os
import random
import string
import sys
import tempfile

from django.core.management import execute_from_command_line


DIRECTORIES = 'var/scratch var/log var/static var/etc var/tmp ' \
              'static templates config ssl service-config'.split()
SERVICE_CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'service-config')


def get_service_config(name):
    with open(os.path.join(SERVICE_CONFIG_DIR, name)) as config:
        return config.read()


def get_defaults():
    return dict(
        secret_key=''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(64)
        ),
        install_dir=os.path.abspath('.'),
        venv_bin_dir=os.path.dirname(sys.executable),
        temp_dir=tempfile.gettempdir(),
    )


def init():
    """Initializes an MDID instance in the current directory"""
    print("Initializing")
    for directory in DIRECTORIES:
        os.makedirs(os.path.join(*directory.split('/')), exist_ok=True)
    defaults = get_defaults()
    settings_file = os.path.join('config', 'settings.py')
    if os.path.exists(settings_file):
        settings_file += '.template'
    with open(settings_file, 'w') as output:
        output.write(get_service_config('mdid') % defaults)
    with open(os.path.join('config', '__init__.py'), 'w') as output:
        pass
    with open(os.path.join('service-config', 'nginx'), 'w') as output:
        output.write(get_service_config('nginx') % defaults)
    with open(os.path.join('service-config', 'supervisor'), 'w') as output:
        output.write(get_service_config('supervisor') % defaults)


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
