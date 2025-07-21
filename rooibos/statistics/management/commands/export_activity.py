from functools import cache

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from rooibos.data.models import Record
from rooibos.statistics.models import AccumulatedActivity
import sys
import csv


class Command(BaseCommand):
    help = """Export accumulated activity"""

    def add_arguments(self, parser):
        parser.add_argument(
            '--type', '-t',
            dest='content_type',
            help='Export activity for this content type '
            '(e.g. record, media, user)'
        )
        parser.add_argument(
            '--year', '-y',
            dest='year',
            help='Export activity for given year only'
        )

    def handle(self, *args, **kwargs):

        content_type = kwargs.get('content_type')

        try:
            content_type_obj = ContentType.objects.get(model=content_type)
        except ContentType.DoesNotExist:
            print("Cannot find given content type '%s'" % content_type)
            sys.exit(1)

        rows = AccumulatedActivity.objects.filter(
            content_type=content_type_obj,
            final=True,
        ).order_by('date', 'id')

        if kwargs.get('year'):
            rows = rows.filter(date__year=kwargs.get('year'))

        row_ids = list(rows.values_list('id', flat=True))
        count = len(row_ids)

        print("Exporting %d rows" % count, file=sys.stderr)

        fields = [
            'type',
            'id',
            'description',
            'date',
            'event',
            'count',
        ]

        writer = csv.DictWriter(sys.stdout, fields)
        writer.writeheader()

        get_description = dict(
            user=lambda user: user.username,
            media=lambda media: media.url,
        ).get(content_type, lambda unknown: '')

        @cache
        def get_description_for_record(item_id):
            try:
                return Record.objects.get(id=item_id).identifier
            except Record.DoesNotExist:
                return ''

        processed = 0
        while processed < count:
            activities_ids = row_ids[processed:processed + 10000]
            activities = AccumulatedActivity.objects.filter(id__in=activities_ids)
            for activity in activities:
                description = ''
                if activity.object_id:
                    if content_type == 'record':
                        description = get_description_for_record(activity.object_id)
                    elif activity.content_object:
                        description = get_description(activity.content_object)
                row = {
                    'type': content_type,
                    'id': activity.object_id,
                    'description': description,
                    'date': activity.date,
                    'event': activity.event,
                    'count': activity.count,
                }
                writer.writerow(row)

            processed += len(activities_ids)
