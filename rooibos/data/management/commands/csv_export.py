
from django.core.management.base import BaseCommand
from rooibos.data.models import Field, Record
import unicodecsv as csv
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    help = 'Export collection metadata'

    def add_arguments(self, parser):
        parser.add_argument('--data', '-d', dest='data_file',
                    help='Output data CSV file')
        parser.add_argument('--collection', '-c', dest='collections',
                    action='append',
                    help='Collection identifier (multiple allowed)')
        parser.add_argument('--separator', '-s', dest='separator',
                    help='Separator for multi-value fields')

    def handle(self, *args, **kwargs):

        data_file = kwargs.get('data_file')
        collections = list(map(int, kwargs.get('collections') or list()))
        separator = kwargs.get('separator')

        fields = list(
            Field.objects
            .filter(fieldvalue__record__collection__in=collections)
            .distinct()
        )

        with open(data_file, 'w') as csvfile:

            fieldnames = [field.full_name for field in fields]
            fieldnames.extend(['__file__', '__path__'])

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            records = Record.objects.filter(collection__in=collections)
            pb = ProgressBar(records.count())

            for count, record in enumerate(records):

                values = record.get_fieldvalues()
                media = list(record.media_set.select_related('storage').all())

                while values or media:
                    row = dict()
                    extra_values = list()

                    for value in values:
                        fieldname = value.field.full_name
                        v = value.value
                        if fieldname in row:
                            if not separator:
                                extra_values.append(value)
                            else:
                                row[fieldname] += separator + v
                        else:
                            row[fieldname] = v

                    if media:
                        m = media.pop()
                        row['__file__'] = m.url
                        row['__path__'] = m.storage.base

                    writer.writerow(row)
                    values = extra_values

                pb.update(count)

            pb.done()
