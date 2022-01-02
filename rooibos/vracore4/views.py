from django.db.models import Q

from ..data.models import Record
from ..util import json_view
from .models import STANDARD_PREFIX, VRACore4FieldValue


def _fieldvalue_as_json(value, extended_data=None):
    result = dict(
        label=value.label,
        fieldLabel=value.field.label,
        hidden=value.hidden,
        dateStart=value.date_start,
        dateEnd=value.date_end,
        value=value.value,
        order=value.order,
        language=value.language,
    )
    if extended_data:
        result.update(dict(

        ))
    return result



    notes = models.TextField(blank=True)
    dataDate = models.DateTimeField(auto_now=True)
    extent = models.TextField(blank=True)
    href = models.TextField(blank=True)
    pref = models.BooleanField(null=True, blank=True)
    refid = models.CharField(max_length=255, blank=True)
    rules = models.CharField(max_length=255, blank=True)
    source = models.TextField(blank=True)
    vocab = models.CharField(max_length=255, blank=True)


def _record_as_json(record, owner=None, context=None, process_url=None):
    process_url = process_url or (lambda url: url)
    fieldvalues = record.get_fieldvalues(owner=owner, context=context, q=Q(field__standard__prefix=STANDARD_PREFIX))
    extended_data = dict((fv.id, fv) for fv in VRACore4FieldValue.objects.filter(id__in=(fv.id for fv in fieldvalues)))

    return dict(
        id=record.id,
        name=record.name,
        title=record.title,
        identifier=record.identifier,
        thumbnail=process_url(record.get_thumbnail_url()),
        image=process_url(record.get_image_url()),
        metadata=[
            _fieldvalue_as_json(value, extended_data.get(value.id))
            for value in fieldvalues
        ]
    )


@json_view
def record(request, id, name):
    record = Record.get_or_404(id, request.user)
    return dict(record=_record_as_json(record, owner=request.user))
