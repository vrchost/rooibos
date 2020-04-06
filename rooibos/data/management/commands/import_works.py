from django.core.management.base import BaseCommand
from rooibos.data.models import Record, Field, FieldValue, standardfield_ids
import csv
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    help = 'Import Archivision works spreadsheet'

    def add_arguments(self, parser):
        parser.add_argument('--mapping', '-m', dest='mapping_file',
                    help='Mapping CSV file')
        parser.add_argument('--collection', '-c', dest='collections',
                    action='append',
                    help='Collection identifier (multiple allowed)')

    def handle(self, *args, **kwargs):

        mapping_file = kwargs.get('mapping_file')
        collections = list(map(int, kwargs.get('collections') or list()))

        if not mapping_file or not collections:
            print("--collection and --mapping are required parameters")
            return

        works = dict()

        with open(mapping_file, 'rU') as mappings:
            reader = csv.DictReader(mappings)
            for row in reader:
                identifier = row['ImageFileName']
                work = row['fk_WorkID']
                works.setdefault(work, []).append(identifier)

        # Clean out old relations
        FieldValue.objects.filter(
            record__collection__in=collections,
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
        ).delete()

        related_field = Field.objects.get(
            standard__prefix='dc',
            name='relation',
        )

        id_fields = standardfield_ids('identifier', equiv=True)

        print("Caching record identifiers")
        identifiers = dict()
        values = FieldValue.objects.select_related('record').filter(
            record__collection__in=collections, field__in=id_fields)
        for fv in values:
            identifiers[fv.value] = fv.record.id

        pb = ProgressBar(len(works))

        # Insert new relations
        for count, work in enumerate(works.values()):
            primary = work[0]
            items = work[1:]
            for item in items:
                options = [item]
                if item.lower().endswith('.jpg'):
                    options.append(item[:-4])
                record = None
                for option in options:
                    record = identifiers.get(option)
                    if record:
                        break
                else:
                    continue
                FieldValue.objects.create(
                    record=Record.objects.get(id=record),
                    field=related_field,
                    refinement='IsPartOf',
                    value=primary
                )

            pb.update(count)

        pb.done()
