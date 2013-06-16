from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rooibos.data.models import Collection
from rooibos.data.functions import collection_dump
from optparse import make_option

class Command(BaseCommand):
    help = 'Dump a collection for later loading in another installation'
    option_list = BaseCommand.option_list + (
        make_option('--collection', '-c', dest='collection',
                    help='Collection'),
        make_option('--prefix', '-p', dest='prefix',
                    help='Prefix for object names, for uniqueness'),
    )


    def handle(self, *args, **kwargs):

        coll = kwargs.get('collection')
        prefix = kwargs.get('prefix')

        if not coll:
            print "--collection is a required parameter"
            return

        if coll.isdigit():
            collection = Collection.objects.get(id=coll)
        else:
            collection = Collection.objects.get(name=coll)

        admins = User.objects.filter(is_superuser=True)
        if admins:
            admin = admins[0]
        else:
            admin = None

        print collection_dump(admin, collection.id, prefix=prefix)
