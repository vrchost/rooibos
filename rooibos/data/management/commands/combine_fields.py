from django.core.management.base import BaseCommand
from rooibos.data.models import Field
from optparse import make_option
import rooibos.contrib.djangologging.middleware # does not get loaded otherwise
import logging


class Command(BaseCommand):
    help = 'Fields and combines equivalent fields'

    option_list = BaseCommand.option_list + (
        make_option('--auto', action='store_true',
            help='Combine automatically detected fields'),
        make_option('--ignorevocabs', action='store_true',
            help='Ignore vocabularis when comparing fields'),
        )

    def handle(self, *commands, **options):
        unique = dict()
        duplicate = 0

        usevocabs = not options.get('ignorevocabs')

        for field in Field.objects.all():

            equivalents = list(field.equivalent.values_list('id', flat=True))
            equivalents.append(field.id)

            key = ' '.join(str(s) for s in [
                field.label,
                field.standard.prefix if field.standard else -1,
                field.vocabulary.id if field.vocabulary and usevocabs else -1,
#                sorted(equivalents)
            ])

            if key in unique:
                duplicate += 1
            else:
                unique[key] = field
                print key

        print "Duplicates found:", duplicate
        print "Uniques:", len(unique)
