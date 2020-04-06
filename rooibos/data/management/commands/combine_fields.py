from django.core.management.base import BaseCommand
from django.db.models import Count
from rooibos.data.models import Field, FieldSetField, FieldValue


class Command(BaseCommand):
    help = 'Finds and combines equivalent fields'

    def add_arguments(self, parser):
        parser.add_argument('--execute', action='store_true',
            help='Combine automatically detected fields',)
        parser.add_argument('--ignorevocabs', action='store_true',
            help='Ignore vocabularies when comparing fields',)
        parser.add_argument('--merge', action='store',
            help='Field to merge into another field',)
        parser.add_argument('--into', action='store',
            help='Field into which to merge another field',)

    def handle(self, *commands, **options):

        execute = options.get('execute')
        merge = options.get('merge')
        into = options.get('into')

        if bool(merge) != bool(into):
            print("--merge and --into must be specified together")
            return

        execute = execute or bool(merge)

        deleted = []
        equivalents = dict()

        def combine_fields(field, replace_with_field):
            print("Replacing %s with %s" % (field, replace_with_field))
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

        print("\nFound %s unique fields out of %s" % (
            len(unique), Field.objects.count()
        ))

        if merge and into:

            merge = Field.objects.get(id=merge)
            into = Field.objects.get(id=into)

            combine_fields(merge, into)

            print("Done")
            return

        # for each unique field, determine replacements

        for fields in list(unique.values()):
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
            print("\nRemaining fields after cleanup:", len(remaining))

        print("\nFields currently in use:\n    Values Field")
        query = FieldValue.objects.values_list(
            'field__id', 'field__name', 'field__standard__prefix'
        )
        query = query.annotate(dcount=Count('field'))
        query = query.order_by('field__standard__prefix', 'field__name')
        for fid, name, prefix, count in query:
            print("%10d %s%s [%d]" % (
                count,
                prefix + "." if prefix else "",
                name,
                fid,
            ))
