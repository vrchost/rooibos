import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from optparse import make_option
import rooibos.contrib.djangologging.middleware # does not get loaded otherwise
from rooibos.userprofile.views import load_settings
import logging
import sys
import json


class Command(BaseCommand):
    help = 'Print user profile settings in JSON format'

    option_list = BaseCommand.option_list + (
        make_option('--user', '-u', dest='user',
                    help='User name'),
    )
    
    def handle(self, *args, **kwargs):

        username = kwargs.get('user')

        if not username:
            print >> sys.stderr, "--user is a required parameter"
            return

        user = User.objects.get(username=username)

        print json.dumps(load_settings(user))
