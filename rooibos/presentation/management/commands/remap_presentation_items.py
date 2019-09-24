from django.core.management.base import BaseCommand
from rooibos.data.models import standardfield_ids, FieldValue
from rooibos.presentation.models import PresentationItem
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--from', '-f',
            dest='from_collection',
            action='store',
            type=int,
            help='Source collection'
        )
        parser.add_argument(
            '--to', '-t',
            dest='to_collections',
            action='append',
            type=int,
            help='Target collection'
        )
        parser.add_argument(
            '--commit', '-c',
            dest='commit',
            action='store_true',
            default=False,
            help='Commit changes'
        )

    help = "Maps presentation items from records in one collection to " \
        "records in another collection. " \
        "Records are compared by their identifier."

    def handle(
            self, from_collection, to_collections, commit, *args, **options):

        if not from_collection or not to_collections:
            print("Error: Must specify --from and --to arguments")
            return

        print("Mapping presentation items from collection %s to " \
            "collection(s) %s" % (from_collection, to_collections))

        idfields = standardfield_ids('identifier', equiv=True)

        print("Fetching identifiers")

        query = FieldValue.objects.filter(
            field__in=idfields,
            record__collectionitem__collection=from_collection,
            owner=None,
            context_type=None,
            hidden=False
        ).values_list('value', 'record')

        record_to_id = dict()
        for identifier, record in query:
            record_to_id.setdefault(record, []).append(identifier)

        print("Fetching target records")

        query = FieldValue.objects.filter(
            field__in=idfields,
            record__collectionitem__collection__in=to_collections,
            owner=None,
            context_type=None,
            hidden=False
        ).values_list('value', 'record')

        id_to_record = dict()

        for identifier, record in query:
            id_to_record.setdefault(identifier, []).append(record)

        print("Mapping presentation items")
        remapped = 0
        errors = []

        items = PresentationItem.objects.filter(
            record__collectionitem__collection=from_collection)
        pb = ProgressBar(len(items))

        for count, item in enumerate(items):
            identifiers = record_to_id.get(item.record_id)
            if identifiers:
                for identifier in identifiers:
                    new_records = id_to_record.get(identifier)
                    if new_records:
                        if len(new_records) == 1:
                            remapped += 1
                            if commit:
                                item.record_id = new_records[0]
                                item.save()
                            break
                        else:
                            errors.append(
                                "Multiple matching records with identifier "
                                "'%s' found in collection %s: %s" %
                                (
                                    identifier,
                                    to_collections,
                                    sorted(new_records)
                                )
                            )
                    else:
                        errors.append(
                            "No record with identifier '%s' found in "
                            "collection %s" % (identifier, to_collections)
                        )
            else:
                errors.append(
                    "No identifier found for record %s" % item.record_id)
            pb.update(count)

        pb.done()

        errors = sorted(set(errors))

        if commit:
            print("Remapped %s items" % remapped)
        else:
            print("Would have remapped %s items - rerun with --commit" % \
                remapped)
        if errors:
            print("%s unique errors occurred:" % len(errors))
            print('\n'.join(errors))
