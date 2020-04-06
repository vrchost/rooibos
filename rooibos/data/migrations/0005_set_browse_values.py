# -*- coding: utf-8 -*-


from django.db import migrations, models, transaction
import re


BROWSE_VALUE_REGEX = re.compile(r"^((a|the|an) +|[^\w]+)+", re.I)

def make_browse_value(value):
    return BROWSE_VALUE_REGEX.sub('', value or '')[:32]


def update_browse_values(apps, schema_editor):
    FieldValue = apps.get_model("data", "FieldValue")

    # TODO: Hack, remove for Django 1.10
    # https://stackoverflow.com/questions/31247810/commit-manually-in-django-data-migration
    schema_editor.connection.in_atomic_block = False

    db_alias = schema_editor.connection.alias
    obj = FieldValue.objects.using(db_alias)
    count = obj.count()
    print()
    idx = 0
    max_id = 0
    while idx < count:
        print("%d/%d (id>%d)" % (idx, count, max_id))
        for f in obj.filter(id__gt=max_id).order_by('id')[:10000]:
            if f.value:
                f.browse_value = make_browse_value(f.value)
                if f.browse_value != f.value[:32]:
                    f.save()
        max_id = f.id if f else 0
        idx += 10000
        transaction.commit()
    print("%d/%d" % (count, count))


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0004_add_browse_value_index'),
    ]

    operations = [
        migrations.RunPython(update_browse_values, migrations.RunPython.noop),
        migrations.RunSQL("UPDATE data_fieldvalue SET browse_value=SUBSTR(value,1,32) WHERE browse_value IS NULL", migrations.RunSQL.noop)
    ]
