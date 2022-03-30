from django.db.models import Q

from ..data.models import Record
from ..util import json_view
from .models import STANDARD_PREFIX, VRACore4FieldValue, STANDARD_MANAGER


def _field_value_as_json(value):
    result = dict(
        id=value.id,
        field=value.field.full_name,
        value=value.value,
        group=value.group,
        notes=value.notes,
        dataDate=value.dataDate,
        extent=value.extent,
        href=value.href,
        pref=value.pref,
        lang=value.lang,
        refid=value.refid,
        rules=value.rules,
        source=value.source,
        vocab=value.vocab,
        type=value.type,
        num=value.num,
        count=value.count,
        unit=value.unit,
        relids=value.relids,
        earliest_date=value.earliest_date,
        earliest_date_circa=value.earliest_date_circa,
        latest_date=value.latest_date,
        latest_date_circa=value.latest_date_circa,
    )
    return {
        key: value
        for key, value in result.items()
        if value is not None and value != ''
    }


def _record_as_json(record, owner=None, context=None, process_url=None):
    process_url = process_url or (lambda url: url)
    field_values = VRACore4FieldValue.objects \
        .filter(record=record, owner=owner) \
        .select_related('field__standard')
    return dict(
        id=record.id,
        name=record.name,
        title=record.title,
        thumbnail=process_url(record.get_thumbnail_url()),
        image=process_url(record.get_image_url()),
        metadata=[
            _field_value_as_json(value)
            for value in field_values
        ]
    )


@json_view
def record_as_json(request, identifier):
    record = Record.get_or_404(identifier, request.user)
    if record.manager != STANDARD_MANAGER:
        return dict(error=f'Record "{identifier}" is not managed by {STANDARD_MANAGER}')
    return dict(record=_record_as_json(record))
