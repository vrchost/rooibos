from django.core.management.base import BaseCommand
from rooibos.storage.models import Media
from rooibos.util.progressbar import ProgressBar

import os
from django.template.defaultfilters import slugify


class Command(BaseCommand):
    help = 'Resets the name property of all Media objects'

    def handle(self, *args, **kwargs):

        updated = 0
        pb = ProgressBar(Media.objects.count())
        for count, media in enumerate(Media.objects.all()):
            name = slugify(os.path.splitext(os.path.basename(media.url))[0])
            if name != media.name:
                media.name = name
                media.save(force_update_name=True)
                updated += 1

            pb.update(count)

        pb.done()

        print("Updated %d media objects" % updated)
