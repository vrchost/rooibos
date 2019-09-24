# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessControl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('read', models.NullBooleanField()),
                ('write', models.NullBooleanField()),
                ('manage', models.NullBooleanField()),
                ('restrictions_repr', models.TextField(default=b'', blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attribute', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=255)),
                ('attribute', models.ForeignKey(to='access.Attribute')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExtendedGroup',
            fields=[
                ('group_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='auth.Group')),
                ('type', models.CharField(max_length=1, choices=[(b'A', b'Authenticated'), (b'I', b'IP Address based'), (b'P', b'Attribute based'), (b'E', b'Everybody')])),
            ],
            options={
            },
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Subnet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subnet', models.CharField(max_length=80)),
                ('group', models.ForeignKey(to='access.ExtendedGroup')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='attribute',
            name='group',
            field=models.ForeignKey(to='access.ExtendedGroup'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='accesscontrol',
            name='usergroup',
            field=models.ForeignKey(blank=True, to='auth.Group', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='accesscontrol',
            unique_together=set([('content_type', 'object_id', 'user', 'usergroup')]),
        ),
    ]
