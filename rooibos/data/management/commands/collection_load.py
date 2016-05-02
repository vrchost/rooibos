from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rooibos.data.functions import collection_load
from sys import stdin


class Command(BaseCommand):
    help = 'Load a collection dump from stdin from another installation'
    option_list = BaseCommand.option_list + ()

    def handle(self, *args, **kwargs):

        admins = User.objects.filter(is_superuser=True)
        if admins:
            admin = admins[0]
        else:
            admin = None

        collection_load(admin, stdin.read())
