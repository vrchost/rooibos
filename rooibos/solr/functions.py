from django.db.models import Min
from rooibos.data.models import get_system_field, FieldValue


class PrimaryWorkRecordManager(object):

    def __init__(self):
        self._works_with_primary_records = None

    def _fetch_works_with_primary_records(self):
        if self._works_with_primary_records is not None:
            return

        records = FieldValue.objects.filter(
            field=get_system_field(),
            label='primary-work-record',
        ).values('record')

        # works that have primary records
        self._works_with_primary_records = set(
            FieldValue.objects.filter(
                field__standard__prefix='dc',
                field__name='relation',
                refinement='IsPartOf',
                record__in=records,
            ).distinct().order_by().values_list('value', flat=True)
        )

    def _works_for_records(self, record_ids):
        return set(
            FieldValue.objects.filter(
                field__standard__prefix='dc',
                field__name='relation',
                refinement='IsPartOf',
                record__in=record_ids,
            ).distinct().order_by().values_list('value', flat=True)
        )

    def get_implicit_primary_work_records(self, record_ids):
        self._fetch_works_with_primary_records()
        works_without_primary_records = (
            self._works_for_records(record_ids) -
            self._works_with_primary_records
        )

        # get records for works without primary records
        primary_records = FieldValue.objects.filter(
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
            value__in=works_without_primary_records,
            index_value__in=(v[:32] for v in works_without_primary_records),
        ).order_by().values('value').annotate(Min('record'))

        return set(pr['record__min'] for pr in primary_records)
