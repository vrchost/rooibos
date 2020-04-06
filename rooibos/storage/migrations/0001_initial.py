# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('data', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.SlugField()),
                ('url', models.CharField(max_length=1024)),
                ('mimetype', models.CharField(default=b'application/binary', max_length=128)),
                ('width', models.IntegerField(null=True)),
                ('height', models.IntegerField(null=True)),
                ('bitrate', models.IntegerField(null=True)),
                ('master', models.ForeignKey(related_name='derivatives', to='storage.Media', null=True)),
                ('record', models.ForeignKey(to='data.Record')),
            ],
            options={
                'verbose_name_plural': 'media',
            },
        ),
        migrations.CreateModel(
            name='ProxyUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', models.CharField(unique=True, max_length=36)),
                ('url', models.CharField(max_length=1024)),
                ('context', models.CharField(max_length=256, null=True, blank=True)),
                ('user_backend', models.CharField(max_length=256, null=True, blank=True)),
                ('last_access', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('name', models.SlugField()),
                ('system', models.CharField(max_length=50)),
                ('base', models.CharField(help_text='Absolute path to server directory containing files.', max_length=1024, null=True)),
                ('urlbase', models.CharField(help_text='URL at which stored file is available, e.g. through streaming. May contain %(filename)s placeholder, which will be replaced with the media url property.', max_length=1024, null=True, verbose_name='URL base', blank=True)),
                ('deliverybase', models.CharField(db_column='serverbase', max_length=1024, blank=True, help_text='Absolute path to server directory in which a temporary symlink to the actual file should be created when the file is requested e.g. for streaming.', null=True, verbose_name='server base')),
                ('derivative', models.IntegerField(null=True, db_column='derivative_id')),
            ],
            options={
                'verbose_name_plural': 'storage',
            },
        ),
        migrations.CreateModel(
            name='TrustedSubnet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subnet', models.CharField(max_length=80)),
            ],
        ),
        migrations.AddField(
            model_name='proxyurl',
            name='subnet',
            field=models.ForeignKey(to='storage.TrustedSubnet'),
        ),
        migrations.AddField(
            model_name='proxyurl',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='media',
            name='storage',
            field=models.ForeignKey(to='storage.Storage'),
        ),
        migrations.AlterUniqueTogether(
            name='media',
            unique_together=set([('record', 'name')]),
        ),
    ]
