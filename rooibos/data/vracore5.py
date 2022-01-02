import re

from .models import Field, MetadataStandard, FieldSetField, FieldSet, FieldValue

STANDARD = 'vra-core-5'
STANDARD_PREFIX = 'vra5'
STANDARD_TITLE = 'VRA Core 5'

FIELDS = """
work
collection
image
agent
agent-attribution
agent-culture
agent-dates
agent-dates-earliestDate
agent-dates-latestDate
agent-name
agent-role
culturalContext
date
date-earliestDate
date-latestDate
description
inscription
inscription-author
inscription-position
inscription-text
location
location-name
location-refid
material
measurements
relation
rights
rights-rightsHolder
rights-text
source
source-name
source-refid
stateEdition
stateEdition-description
stateEdition-name
stylePeriod
subject
subject-term
technique
textref
textref-name
textref-refid
title
worktype
"""


def create_data_fixtures(sender, *args, **kwargs):
    """
    Signal handler
    """
    create_vra_core_5_fields()


def _format_label(name):
    return ' '.join(n.capitalize() for n in re.sub(r'([A-Z])', r' \1', name).replace('-', ' ').split(' '))


def create_vra_core_5_fields():

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
        fields[field_name], _ = Field.objects.get_or_create(
            name=field_name,
            standard=standard,
            defaults=dict(
                label=_format_label(field_name),
            )
        )
        FieldSetField.objects.get_or_create(
            fieldset=fieldset,
            field=fields[field_name],
            defaults=dict(
                order=(index + 1) * 10,
                label=fields[field_name].label,
            )
        )

    # TODO: dc field equivalents
