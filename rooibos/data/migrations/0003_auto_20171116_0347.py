# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0002_auto_20171028_0959'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldvalue',
            name='browse_value',
            field=models.CharField(serialize=False, max_length=32, null=True, db_index=True),
        ),
        migrations.AlterIndexTogether(
            name='fieldvalue',
            index_together=set([('field', 'record', 'browse_value'), ('field', 'record', 'index_value'), ('record', 'field')]),
        ),
    ]
