from django.core.management.base import BaseCommand
from rooibos.data.models import FieldValue, standardfield
from rooibos.util.progressbar import ProgressBar

from django.template.defaultfilters import slugify


class Command(BaseCommand):
    help = 'Resets the name property of all Record objects'

    def handle(self, *args, **kwargs):

        updated = 0

        id_fields = standardfield('identifier', equiv=True)
        titles = FieldValue.objects.select_related('record').filter(
            field__in=id_fields)
        pb = ProgressBar(titles.count())

        for count, title in enumerate(titles):
            name = slugify(title.value)
            if name != title.record.name:
                title.record.name = name
                title.record.save(force_update_name=True)
                updated += 1

            pb.update(count)

        pb.done()

        print("Updated %d record objects" % updated)
