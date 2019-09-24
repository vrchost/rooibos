# -*- coding: utf-8 -*-


from django.db import migrations


def remove_equivalency(apps, schema_editor):
    Field = apps.get_model("data", "Field")
    try:
        f = Field.objects.get(name='title', standard__prefix='vra')
        Field.objects.get(name='title', standard__prefix='dc') \
            .equivalent.remove(f)
    except Field.DoesNotExist:
        pass
    try:
        f = Field.objects.get(name='title', standard__prefix='dc')
        Field.objects.get(name='title', standard__prefix='vra') \
            .equivalent.remove(f)
    except Field.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0009_remove_dc_vra_equivalent_field'),
    ]

    operations = [
        migrations.RunPython(remove_equivalency, migrations.RunPython.noop),
    ]
