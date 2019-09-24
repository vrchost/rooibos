from django.core.management.base import BaseCommand
from rooibos.storage.models import Media
from django.contrib.contenttypes.models import ContentType
from rooibos.migration.models import ObjectHistory
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--check', '-c',
            dest='check',
            action='store_true',
            help='Check for unneeded media'
        )
        parser.add_argument(
            '--remove', '-r',
            dest='remove',
            action='store_true',
            help='Remove unneeded media'
        )

    help = "Removes unneeded media objects migrated from MDID 2"

    def handle(self, check, remove, *args, **options):
        if check == remove:
            print("Error: must specify exactly one of --check or --remove")
        elif check:
            self.check()
        elif remove:
            self.remove()

    def check(self):

        print("Checking...")

        content_type = ContentType.objects.get_for_model(Media)
        migrated = set(ObjectHistory.objects.filter(
            content_type=content_type).values_list('object_id', flat=True))
        full = set(Media.objects.filter(
            url__startswith="full\\").values_list('id', flat=True))
        medium = set(Media.objects.filter(
            url__startswith="medium\\").values_list('id', flat=True))
        thumb = set(Media.objects.filter(
            url__startswith="thumb\\").values_list('id', flat=True))

        full_records = set(Media.objects.filter(
            url__startswith="full\\").values_list('record', flat=True))
        medium_records = set(Media.objects.filter(
            url__startswith="medium\\").values_list('record', flat=True))
        thumb_records = set(Media.objects.filter(
            url__startswith="thumb\\").values_list('record', flat=True))

        print("Found %d migrated media objects - these are ok" % len(migrated))
        print("Found %d full media objects" % len(full))
        print("Found %d medium media objects" % len(medium))
        print("Found %d thumb media objects" % len(thumb))
        print()

        full = full - migrated
        medium = medium - migrated
        thumb = thumb - migrated

        print("Found %d non-migrated full media objects" % len(full))
        print("Found %d non-migrated medium media objects" % len(medium))
        print("Found %d non-migrated thumb media objects" % len(thumb))
        print()

        common = full_records & medium_records & thumb_records

        print("Found %d records with three sizes of media" % len(common))

        return common

    def remove(self):

        common = self.check()

        print("Removing unneeded media objects")

        pb = ProgressBar(len(common))
        count = 0

        for id in common:
            m = Media.objects.filter(record__id=id)
            m.filter(url__startswith='medium\\').delete()
            m.filter(url__startswith='thumb\\').delete()
            count += 1
            pb.update(count)

        pb.done()
