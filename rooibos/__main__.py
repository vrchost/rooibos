import os
import random
import shutil
import string
import sys
import tempfile

from django.core.management import execute_from_command_line


DIRECTORIES = 'var/scratch var/log var/static var/etc var/tmp var/www ' \
              'static templates ssl service-config'.split()
CODE_DIRECTORIES = 'config lib'.split()
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
    for directory in DIRECTORIES + CODE_DIRECTORIES:
        os.makedirs(os.path.join(*directory.split('/')), exist_ok=True)
    for code_dir in CODE_DIRECTORIES:
        with open(os.path.join(*code_dir.split('/'), '__init__.py'), 'w'):
            pass
    defaults = get_defaults()
    settings_file = os.path.join('config', 'settings.py')
    if os.path.exists(settings_file):
        settings_file += '.template'
    with open(settings_file, 'w') as output:
        output.write(get_service_config('mdid') % defaults)
    for service in os.listdir(SERVICE_CONFIG_DIR):
        service_path = os.path.join(SERVICE_CONFIG_DIR, service)
        if os.path.isfile(service_path) and service != 'mdid':
            with open(os.path.join('service-config', service), 'w') as output:
                output.write(get_service_config(service) % defaults)
    if not os.path.exists(os.path.join('var', 'solr')):
        shutil.copytree(
            os.path.join(SERVICE_CONFIG_DIR, 'solr7'),
            os.path.join('var', 'solr')
        )


def main():
    """Run MDID and Django admin commands"""
    python_path = os.getenv('PYTHONPATH')
    if not python_path:
        paths = {'.'}
        # look for config directory above where this file is
        path = os.path.dirname(__file__)
        while not os.path.exists(os.path.join(path, 'config', 'settings.py')):
            new_path = os.path.dirname(path)
            if new_path == path:
                # reached top, give up and just use current directory
                path = '.'
                break
            path = new_path
        paths.add(path)
        os.putenv('PYTHONPATH', os.pathsep.join(paths))
        for path in paths:
            sys.path.append(path)

    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        init()
        sys.exit(0)

    settings_module = os.getenv('DJANGO_SETTINGS_MODULE')
    if not settings_module:
        try:
            import config.settings  # noqa: F401
            os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
        except ImportError:
            print('Could not find MDID settings, have you run "mdid init"?')
            sys.exit(1)
    sys.exit(execute_from_command_line())
