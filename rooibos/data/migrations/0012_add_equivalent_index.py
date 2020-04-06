# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0011_auto_20190106_0837'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX idx_from_field_id ON data_field_equivalent (from_field_id)",
            "DROP INDEX idx_from_field_id ON data_field_equivalent"
        ),
    ]
