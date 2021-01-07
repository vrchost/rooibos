import argparse
import os
import random
import string
import sys
from django.core.management import execute_from_command_line


DIRECTORIES = 'scratch storage log static templates config'.split()

CONFIG = """
from rooibos.settings.base import *

SECRET_KEY = '%(secret_key)s'
"""


def main():
    parser = argparse.ArgumentParser(prog='mdid')
    parser.add_argument(
        'command', help='Command to run', choices=['init', 'admin'])
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()
    globals()[args.command]()


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
    )
    settings_file = os.path.join('config', 'settings.py')
    if not os.path.exists(settings_file):
        with open(settings_file, 'w') as output:
            output.write(CONFIG % defaults)
    with open(os.path.join('config', '__init__.py'), 'w') as output:
        pass


def admin():
    """Run MDID and Django admin commands"""
    python_path = os.getenv('PYTHONPATH')
    if not python_path:
        os.putenv('PYTHONPATH', '.')
        sys.path.append('.')
    settings_module = os.getenv('DJANGO_SETTINGS_MODULE')
    if not settings_module:
        try:
            import config.settings
        except ImportError:
            print('Could not find MDID settings, have you run "mdid init"?')
            return 1
        os.putenv('DJANGO_SETTINGS_MODULE', 'config.settings')
    sys.argv = ['django-admin'] + sys.argv[2:]
    sys.exit(execute_from_command_line())
