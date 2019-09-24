from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rooibos.userprofile.views import load_settings
import sys
import json


class Command(BaseCommand):
    help = 'Print user profile settings in JSON format'

    def add_arguments(self, parser):
        parser.add_argument('--user', '-u', dest='user',
                    help='User name'),

    def handle(self, *args, **kwargs):

        username = kwargs.get('user')

        if not username:
            print("--user is a required parameter", file=sys.stderr)
            return

        user = User.objects.get(username=username)

        print(json.dumps(load_settings(user)))
