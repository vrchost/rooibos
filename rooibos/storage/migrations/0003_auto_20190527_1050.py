# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_remove_storage_derivative'),
    ]

    operations = [
        migrations.AddField(
            model_name='storage',
            name='credential_id',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='storage',
            name='credential_key',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
