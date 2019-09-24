from django.core.management.base import BaseCommand
from rooibos.storage.models import Storage


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--list', '-l',
            dest='list',
            action='store_true',
            help='List current storage paths'
        )
        parser.add_argument(
            '--prefix', '-p',
            dest='prefix',
            help='Prefix to replace or filter by'
        )
        parser.add_argument(
            '--replace-with', '-r',
            dest='replace',
            help='Replacement prefix'
        )
        parser.add_argument(
            '--simulate', '-s',
            dest='simulate',
            action='store_true',
            help='Simulate only'
        )

    help = "Fixes storage (resource) paths after migration " \
           "or other move of image files"

    def handle(self, list, prefix, replace, simulate, *args, **options):
        if list or not replace:
            self.list(prefix)
        elif prefix:
            self.replace(prefix, replace, simulate)
        else:
            print("Error: must specify --list " \
                  "or both --prefix and --replace-with")

    def list(self, prefix):
        for storage in Storage.objects.filter(
                system='local', base__startswith=prefix or ''):
            print("%s: %s" % (storage.name, storage.base))

    def replace(self, prefix, replace, simulate):
        for storage in Storage.objects.filter(
                system='local', base__startswith=prefix or ''):
            new_base = replace + storage.base[len(prefix):]
            print("%s: %s -> %s" % (storage.name, storage.base, new_base))
            if not simulate:
                storage.base = new_base
                storage.save()
