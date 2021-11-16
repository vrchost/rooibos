import csv
import io

from django.core.management.base import BaseCommand

from rooibos.data.models import FieldValue, Field, Collection


class Command(BaseCommand):
    help = 'Outputs usage of fields in collections for further processing ' \
           'in a pivot table'

    def handle(self, *args, **kwargs):

        outfile = io.StringIO()
        outcsv = csv.writer(outfile)
        outcsv.writerow(['Collection', 'Field Identifier', 'Field', 'Count'])

        for f in Field.objects.all():
            for c in Collection.objects.all():
                count = FieldValue.objects.filter(
                    field=f, record__collection=c).count()
                if count > 0:
                    outcsv.writerow([c.title, f.id, f.full_name, str(count)])

        print(outfile.getvalue())
