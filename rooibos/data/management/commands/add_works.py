from django.core.management.base import BaseCommand
from rooibos.data.models import Field, FieldValue, standardfield_ids, \
    get_system_field
import csv
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    help = 'Import Archivision works spreadsheet'

    def add_arguments(self, parser):
        parser.add_argument(
            '--collection',
            '-c',
            dest='collections',
            action='append',
            help='Collection identifier (multiple allowed)'
        )
        parser.add_argument(
            '--mapping',
            '-m',
            dest='mapping_file',
            action='store',
            help='File mapping identifiers to works'
        )

    def handle(self, *args, **kwargs):

        system_field = get_system_field()

        collections = list(map(int, kwargs.get('collections') or list()))
        mapping_file = kwargs.get('mapping_file')

        if not collections:
            print("--collection is a required parameter")
            return

        if not mapping_file:
            print("--mapping is a required parameter")
            return

        mappings = dict()
        with open(mapping_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                mappings[row['Identifier']] = (row['Work'], row['Primary'])

        related_field = Field.objects.get(
            standard__prefix='dc',
            name='relation',
        )

        existing_works = FieldValue.objects.filter(
            record__collection__in=collections,
            field=related_field,
            refinement='IsPartOf',
        )

        # Clean out old relations
        print("Deleting old works info")
        existing_works.delete()

        id_fields = standardfield_ids('identifier', equiv=True)

        print("Fetching records")
        identifiers = FieldValue.objects.select_related('record').filter(
            record__collection__in=collections,
            field__in=id_fields,
        )

        pb = ProgressBar(identifiers.count())

        # Insert new relations
        for count, identifier in enumerate(identifiers):

            work, isprimary = mappings.get(identifier.value, (None, False))
            isprimary = isprimary == 'True'
            if not work:
                print("Warning: no entry found for identifier '%s'" % \
                      identifier.value)
                continue

            FieldValue.objects.create(
                record=identifier.record,
                field=related_field,
                refinement='IsPartOf',
                value=work,
                hidden=True
            )

            fv = list(FieldValue.objects.filter(
                record=identifier.record,
                field=system_field,
                label='primary-work-record'
            ))
            if len(fv) > 0:
                if not isprimary:
                    for f in fv:
                        f.delete()
            elif isprimary:
                FieldValue.objects.create(
                    record=identifier.record,
                    field=system_field,
                    label='primary-work-record',
                    value=work,
                    hidden=True,
                )

            pb.update(count)

        pb.done()
