# -*- coding: utf-8 -*-


from django.db import migrations


def remove_equivalency(apps, schema_editor):
    Field = apps.get_model("data", "Field")
    try:
        f = Field.objects.get(name='styleperiod', standard__prefix='vra')
        Field.objects.get(name='subject', standard__prefix='dc') \
            .equivalent.remove(f)
    except Field.DoesNotExist:
        pass
    try:
        f = Field.objects.get(name='subject', standard__prefix='dc')
        Field.objects.get(name='styleperiod', standard__prefix='vra') \
            .equivalent.remove(f)
    except Field.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0008_system_standard_and_alt_text_field'),
    ]

    operations = [
        migrations.RunPython(remove_equivalency, migrations.RunPython.noop),
    ]
