from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option
from rooibos.userprofile.views import store_settings
import sys
import json


class Command(BaseCommand):
    help = 'Imports user profile settings in JSON format from stdin'

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

        s = json.loads(' '.join(sys.stdin.readlines()))

        for k, v in s.iteritems():
            print "Importing %s" % k
            store_settings(user, k, v[0])
