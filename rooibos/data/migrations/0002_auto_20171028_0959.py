# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='fieldvalue',
            index_together=set([('field', 'record', 'index_value'), ('record', 'field')]),
        ),
    ]
