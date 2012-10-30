import models as data_app
from django.db.models import signals
from models import MetadataStandard, Field, FieldSet, FieldSetField


def create_data_fixtures(*args, **kwargs):
    print "Creating data fixtures"

    # Metadata standars

    dc, created = MetadataStandard.objects.get_or_create(
        name='dublin-core',
        defaults=dict(
            prefix='dc',
            title='Dublin Core',
        )
    )

    tag, created = MetadataStandard.objects.get_or_create(
        name='tagging',
        defaults=dict(
            prefix='tag',
            title='Tagging',
        )
    )

    vra, created = MetadataStandard.objects.get_or_create(
        name='vra-core-4',
        defaults=dict(
            prefix='vra',
            title='VRA Core 4',
        )
    )

    # Fieldsets

    dcfs, created = FieldSet.objects.get_or_create(
        name='dc',
        defaults=dict(
            standard=1,
            title='Dublin Core',
        )
    )

    vrafs, created = FieldSet.objects.get_or_create(
        name='vra-core-4',
        defaults=dict(
            standard=1,
            title='VRA Core 4',
        )
    )

    # Fields

    fields = [
        (1, [17, 22], dc, "contributor", "Contributor"),
        (2, [18, 19, 22, 29], dc, "coverage", "Coverage"),
        (3, [17], dc, "creator", "Creator"),
        (4, [19], dc, "date", "Date"),
        (5, [20], dc, "description", "Description"),
        (6, [23, 24, 31], dc, "format", "Format"),
        (7, [32], dc, "identifier", "Identifier"),
        (8, [], dc, "language", "Language"),
        (9, [], dc, "publisher", "Publisher"),
        (10, [25], dc, "relation", "Relation"),
        (11, [26], dc, "rights", "Rights"),
        (12, [27], dc, "source", "Source"),
        (13, [16,29,30], dc, "subject", "Subject"),
        (14, [33], dc, "title", "Title"),
        (15, [34], dc, "type", "Type"),
        (16, [13], tag, "tags", "Tags"),
        (17, [1, 3], vra, "agent", "Agent"),
        (18, [2], vra, "culturalcontext", "Cultural Context"),
        (19, [2, 4], vra, "date", "Date"),
        (20, [5], vra, "description", "Description"),
        (21, [], vra, "inscription", "Inscription"),
        (22, [1, 2], vra, "location", "Location"),
        (23, [6], vra, "material", "Material"),
        (24, [6], vra, "measurements", "Measurements"),
        (25, [10], vra, "relation", "Relation"),
        (26, [11], vra, "rights", "Rights"),
        (27, [12], vra, "source", "Source"),
        (28, [], vra, "stateedition", "State/Edition"),
        (29, [2,13], vra, "styleperiod", "Style/Period"),
        (30, [13], vra, "subject", "Subject"),
        (31, [6], vra, "technique", "Technique"),
        (32, [7], vra, "textref", "Textual Reference"),
        (33, [14], vra, "title", "Title"),
        (34, [15], vra, "worktype", "Work Type"),
    ]

    f = dict()
    for id, equiv, standard, name, label in fields:
        f[id], created = Field.objects.get_or_create(
            name=name,
            standard=standard,
            defaults=dict(
                label=label,
            )
        )
    for id, equiv, standard, name, label in fields:
        for e in equiv:
            f[id].equivalent.add(f[e])

    # Fieldset fields

    fieldsetfields = [
        (1, 34, vrafs, 0),
        (1, 20, vrafs, 0),
        (1, 21, vrafs, 0),
        (1, 22, vrafs, 0),
        (1, 23, vrafs, 0),
        (1, 24, vrafs, 0),
        (1, 25, vrafs, 0),
        (1, 26, vrafs, 0),
        (1, 27, vrafs, 0),
        (1, 28, vrafs, 0),
        (1, 29, vrafs, 0),
        (1, 30, vrafs, 0),
        (1, 31, vrafs, 0),
        (1, 32, vrafs, 0),
        (1, 33, vrafs, 0),
        (1, 19, vrafs, 0),
        (1, 18, vrafs, 0),
        (1, 17, vrafs, 0),
        (1, 7, dcfs, 1),
        (10, 14, dcfs, 2),
        (10, 5, dcfs, 3),
        (10, 3, dcfs, 4),
        (8, 2, dcfs, 5),
        (8, 4, dcfs, 6),
        (6, 15, dcfs, 7),
        (8, 13, dcfs, 8),
        (1, 1, dcfs, 9),
        (6, 6, dcfs, 10),
        (1, 8, dcfs, 11),
        (1, 9, dcfs, 12),
        (1, 11, dcfs, 13),
        (1, 10, dcfs, 14),
        (1, 12, dcfs, 15),
    ]

    for importance, field, fieldset, order in fieldsetfields:
        FieldSetField.objects.get_or_create(
            fieldset=fieldset,
            field=f[field],
            defaults=dict(
                importance=importance,
                order=order,
            )
        )


signals.post_syncdb.connect(create_data_fixtures, sender=data_app)
