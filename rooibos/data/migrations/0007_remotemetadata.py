# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '__first__'),
        ('data', '0006_auto_20171121_0410'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteMetadata',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=255)),
                ('mapping_url', models.CharField(max_length=255)),
                ('last_modified', models.CharField(max_length=100, null=True, blank=True)),
                ('collection', models.ForeignKey(to='data.Collection')),
                ('storage', models.ForeignKey(to='storage.Storage')),
            ],
        ),
    ]
