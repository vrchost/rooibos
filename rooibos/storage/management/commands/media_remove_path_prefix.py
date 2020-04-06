from django.core.management.base import BaseCommand
from django.db import reset_queries
from rooibos.storage.models import Media
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    help = 'Removes given prefix from all media objects'
    args = 'prefix'

    def handle(self, *prefix, **options):
        if not prefix:
            print(self.help)
        else:
            count = updated = 0
            total = Media.objects.count()
            pb = ProgressBar(total)
            for i in range(0, total, 100):
                for media in Media.objects.all()[i:i + 100]:
                    if media.url.startswith(prefix):
                        media.url = media.url[len(prefix):]
                        media.save()
                        updated += 1
                    count += 1
                    pb.update(count)
                reset_queries()
            pb.done()
            print("Updated %d/%d media objects" % (updated, count))
