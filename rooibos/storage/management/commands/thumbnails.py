from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rooibos.data.models import Collection
from rooibos.storage.functions import get_thumbnail_for_record
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    help = 'Pre-builds thumbnails for a collection'

    def add_arguments(self, parser):
        parser.add_argument('--collection', '-c', dest='collection',
                    help='Collection')


    def handle(self, *args, **kwargs):

        coll = kwargs.get('collection')

        if not coll:
            print("--collection is a required parameter")
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

        pb = ProgressBar(collection.records.count())
        for count, record in enumerate(collection.records.all()):

            get_thumbnail_for_record(record, admin)
            get_thumbnail_for_record(record, admin, crop_to_square=True)

            pb.update(count)

        pb.done()
