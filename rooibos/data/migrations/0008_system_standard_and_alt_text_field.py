# -*- coding: utf-8 -*-


from django.db import migrations


def create_field(apps, schema_editor):
    MetadataStandard = apps.get_model("data", "MetadataStandard")
    standard, _ = MetadataStandard.objects.get_or_create(
        name='system',
        defaults=dict(
            title='System',
            prefix='system',
        ),
    )
    Field = apps.get_model("data", "Field")
    Field.objects.get_or_create(
        name='alt-text',
        standard=standard,
        defaults=dict(
            label='Alt Text',
        ),
    )


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0007_remotemetadata'),
    ]

    operations = [
        migrations.RunPython(create_field, migrations.RunPython.noop),
    ]
