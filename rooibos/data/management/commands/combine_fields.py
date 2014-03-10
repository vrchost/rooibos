from django.core.management.base import BaseCommand
from django.db.models import Count
from rooibos.data.models import Field, FieldSetField, FieldValue
from optparse import make_option


class Command(BaseCommand):
    help = 'Fields and combines equivalent fields'

    option_list = BaseCommand.option_list + (
        make_option(
            '--execute', action='store_true',
            help='Combine automatically detected fields'),
        make_option(
            '--ignorevocabs', action='store_true',
            help='Ignore vocabularies when comparing fields'),
        )

    def handle(self, *commands, **options):

        execute = options.get('execute')

        deleted = []
        equivalents = dict()

        def combine_fields(field, replace_with_field):
            print "Replacing %s with %s" % (field, replace_with_field)
            deleted.append(field.id)
            eq = list(field.equivalent.values_list('id', flat=True))
            equivalents[replace_with_field] = equivalents.get(
                replace_with_field, set()).union(set(eq))
            if execute:
                # replace equivalence references
                for f in Field.objects.filter(equivalent=field):
                    f.equivalent.add(replace_with_field)
                    f.equivalent.remove(field)
                # replace field references
                FieldSetField.objects.filter(field=field).update(
                    field=replace_with_field)
                FieldValue.objects.filter(field=field).update(
                    field=replace_with_field)
                field.delete()

        unique = dict()

        usevocabs = not options.get('ignorevocabs')

        for field in Field.objects.all():

            key = ' '.join([
                field.label,
                field.standard.prefix if field.standard else "-",
                str(field.vocabulary.id) if field.vocabulary and usevocabs
                else "-",
            ])

            unique.setdefault(key, []).append(field)

        print "\nFound %s unique fields out of %s" % (
            len(unique), Field.objects.count()
            )

        # for each unique field, determine replacements

        for fields in unique.values():
            if len(fields) < 2:
                continue
            sorted_fields = sorted(fields, key=lambda f: f.name)
            keep = sorted_fields[0]
            for remove in sorted_fields[1:]:
                combine_fields(remove, keep)

        # now go through remaining fields and replace the ones that are not
        # standard fields with their standard equivalents, if any

        for field in Field.objects.exclude(id__in=deleted):
            if field.standard:
                continue
            eq = equivalents.get(field, set()).union(
                field.equivalent.values_list('id', flat=True))
            eqfields = Field.objects.filter(id__in=eq).exclude(
                id__in=deleted).exclude(standard=None).filter(
                label=field.label)
            if usevocabs:
                eqfields = eqfields.filter(vocabulary=field.vocabulary)
            if eqfields:
                combine_fields(field, eqfields[0])

        if execute:
            remaining = Field.objects.exclude(id__in=deleted)
            print "\nRemaining fields after cleanup:", len(remaining)

        print "\nFields currently in use:\n    Values Field"
        for name, prefix, count in FieldValue.objects.values_list(
                'field__name', 'field__standard__prefix').annotate(
                dcount=Count('field')).order_by(
                'field__standard__prefix', 'field__name'):
            print "%10d %s%s" % (count, prefix + "." if prefix else "", name)
