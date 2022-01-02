import re

from django.db import models
from django.db.models import signals

from ..data.models import Field, MetadataStandard, FieldSetField, FieldSet, FieldValue, standardfield


class VRACore4FieldValue(FieldValue):
    notes = models.TextField(blank=True)
    dataDate = models.CharField(max_length=255, blank=True)
    extent = models.TextField(blank=True)
    href = models.TextField(blank=True)
    pref = models.BooleanField(null=True, blank=True)
    lang = models.CharField(max_length=255, blank=True)
    refid = models.CharField(max_length=255, blank=True)
    rules = models.CharField(max_length=255, blank=True)
    source = models.TextField(blank=True)
    vocab = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=255, blank=True)
    num = models.CharField(max_length=255, blank=True)
    count = models.CharField(max_length=255, blank=True)
    unit = models.CharField(max_length=255, blank=True)
    relids = models.CharField(max_length=255, blank=True)
    earliest_date = models.CharField(max_length=255, blank=True)
    earliest_date_circa = models.BooleanField(null=True, blank=True)
    latest_date = models.CharField(max_length=255, blank=True)
    latest_date_circa = models.BooleanField(null=True, blank=True)


STANDARD = 'vra-core-4-00'
STANDARD_PREFIX = 'vra400'
STANDARD_TITLE = 'VRA Core 4 (rev 00)'
STANDARD_NAMESPACE = 'http://www.vraweb.org/vracore4.htm'
STANDARD_MANAGER = f'{STANDARD}-manager'

FIELDS = """
work
collection
image
agentSet
agent-notes
agent-attribution
agent-culture
agent-dates
agent-dates-earliestDate
agent-dates-latestDate
agent-name
agent-role
culturalContextSet
culturalContext-notes
culturalContext
dateSet
date-notes
date
descriptionSet
description-notes
description
inscriptionSet
inscription-notes
inscription-author
inscription-position
inscription-text
locationSet
location-notes
location-name
location-refid
location
materialSet
material-notes
measurementsSet
measurements-notes
measurements
relationSet
relation-notes
relation
rightsSet
rights-notes
rights-rightsHolder
rights-text
sourceSet
source-notes
source-name
source-refid
stateEditionSet
stateEdition-notes
stateEdition-description
stateEdition-name
stylePeriodSet
stylePeriod-notes
stylePeriod
subjectSet
subject-notes
subject-term
techniqueSet
technique-notes
technique
textrefSet
textref-notes
textref-name
textref-refid
titleSet
title-notes
title
worktypeSet
worktype-notes
worktype
"""


def create_data_fixtures(sender, *args, **kwargs):
    """
    Signal handler
    """
    create_vra_core_4_fields()


def _format_label(name):
    name = name.replace('Set', '').replace('-', ' ')
    name = re.sub(r'([A-Z])', r' \1', name)
    return ' '.join(n.capitalize() for n in name.split(' '))


def create_vra_core_4_fields():

    dc_id_field = standardfield('identifier')
    dc_title_field = standardfield('title')

    standard, _ = MetadataStandard.objects.get_or_create(
        name=STANDARD,
        defaults=dict(
            prefix=STANDARD_PREFIX,
            title=STANDARD_TITLE,
        )
    )

    fieldset, _ = FieldSet.objects.get_or_create(
        name=STANDARD,
        defaults=dict(
            standard=True,
            title=STANDARD_TITLE,
        )
    )

    fields = dict()
    for index, field_name in enumerate(n for n in FIELDS.split('\n') if n):
        field_label = _format_label(field_name)
        fields[field_name], _ = Field.objects.get_or_create(
            name=field_name,
            standard=standard,
            defaults=dict(
                label=field_label,
            )
        )
        FieldSetField.objects.get_or_create(
            fieldset=fieldset,
            field=fields[field_name],
            defaults=dict(
                order=(index + 1) * 10,
                label=field_label,
            )
        )

    fields['titleSet'].equivalent.add(dc_title_field)
    fields['work'].equivalent.add(dc_id_field)
    fields['collection'].equivalent.add(dc_id_field)
    fields['image'].equivalent.add(dc_id_field)


signals.post_migrate.connect(create_data_fixtures)
