# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0005_set_browse_values'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldvalue',
            name='browse_value',
            field=models.CharField(max_length=32, serialize=False, db_index=True),
        ),
    ]
