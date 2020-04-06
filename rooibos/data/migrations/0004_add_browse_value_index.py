# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0003_auto_20171116_0347'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='fieldvalue',
            index_together=set([('field', 'record', 'browse_value'), ('field', 'record', 'index_value'), ('record', 'field')]),
        ),
    ]
