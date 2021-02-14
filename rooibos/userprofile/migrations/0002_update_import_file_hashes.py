# -*- coding: utf-8 -*-
import json

from django.db import migrations, transaction

from rooibos.util import calculate_hash


def update_hashes(apps, schema_editor):
    Preference = apps.get_model("userprofile", "Preference")

    used = dict()
    for pref in list(
            Preference.objects.filter(setting__startswith='data_import_file_')):
        used[pref.setting] = True

    for pref in list(
            Preference.objects.filter(setting__startswith='data_import_file_')):
        hash = 'data_import_file_' + calculate_hash('\t'.join(
            sorted(
                [f['fieldname'] for f in json.loads(pref.value)['mapping']])))
        if hash not in used:
            pref.setting = hash
            pref.save()
            used[hash] = True


class Migration(migrations.Migration):
    dependencies = [
        ('userprofile', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(update_hashes, migrations.RunPython.noop),
    ]
