# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('name', models.SlugField(unique=True, blank=True)),
                ('hidden', models.BooleanField(default=False, serialize=False)),
                ('description', models.TextField(blank=True)),
                ('agreement', models.TextField(null=True, blank=True)),
                ('password', models.CharField(max_length=32, blank=True)),
                ('order', models.IntegerField(default=100)),
                ('children', models.ManyToManyField(to='data.Collection', serialize=False, blank=True)),
                ('owner', models.ForeignKey(serialize=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['order', 'title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CollectionItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hidden', models.BooleanField(default=False)),
                ('collection', models.ForeignKey(to='data.Collection')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Field',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=100)),
                ('name', models.SlugField()),
                ('old_name', models.CharField(serialize=False, max_length=100, null=True, blank=True)),
                ('equivalent', models.ManyToManyField(related_name='equivalent_rel_+', null=True, to='data.Field', blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('name', models.SlugField()),
                ('standard', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldSetField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=100, null=True, blank=True)),
                ('order', models.IntegerField(default=0)),
                ('importance', models.SmallIntegerField(default=1)),
                ('field', models.ForeignKey(to='data.Field')),
                ('fieldset', models.ForeignKey(to='data.FieldSet')),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FieldValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('refinement', models.CharField(max_length=100, null=True, blank=True)),
                ('label', models.CharField(max_length=100, null=True, blank=True)),
                ('hidden', models.BooleanField(default=False)),
                ('order', models.IntegerField(default=0)),
                ('group', models.IntegerField(null=True, blank=True)),
                ('value', models.TextField()),
                ('index_value', models.CharField(max_length=32, serialize=False, db_index=True)),
                ('date_start', models.DecimalField(null=True, max_digits=12, decimal_places=0, blank=True)),
                ('date_end', models.DecimalField(null=True, max_digits=12, decimal_places=0, blank=True)),
                ('numeric_value', models.DecimalField(null=True, max_digits=18, decimal_places=4, blank=True)),
                ('language', models.CharField(max_length=5, null=True, blank=True)),
                ('context_id', models.PositiveIntegerField(serialize=False, null=True, blank=True)),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DisplayFieldValue',
            fields=[
                ('fieldvalue_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='data.FieldValue')),
            ],
            options={
            },
            bases=('data.fieldvalue',),
        ),
        migrations.CreateModel(
            name='MetadataStandard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('name', models.SlugField(unique=True)),
                ('prefix', models.CharField(unique=True, max_length=16)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Record',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.SlugField(unique=True)),
                ('source', models.CharField(max_length=1024, null=True, blank=True)),
                ('manager', models.CharField(max_length=50, null=True, blank=True)),
                ('next_update', models.DateTimeField(serialize=False, null=True, blank=True)),
                ('owner', models.ForeignKey(serialize=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('parent', models.ForeignKey(blank=True, to='data.Record', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Vocabulary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('name', models.SlugField()),
                ('description', models.TextField(null=True, blank=True)),
                ('standard', models.NullBooleanField()),
                ('origin', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'vocabularies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VocabularyTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('term', models.TextField()),
                ('vocabulary', models.ForeignKey(to='data.Vocabulary')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='fieldvalue',
            name='context_type',
            field=models.ForeignKey(serialize=False, blank=True, to='contenttypes.ContentType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fieldvalue',
            name='field',
            field=models.ForeignKey(to='data.Field'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fieldvalue',
            name='owner',
            field=models.ForeignKey(serialize=False, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fieldvalue',
            name='record',
            field=models.ForeignKey(editable=False, to='data.Record'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fieldset',
            name='fields',
            field=models.ManyToManyField(to='data.Field', through='data.FieldSetField'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='fieldset',
            name='owner',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='field',
            name='standard',
            field=models.ForeignKey(blank=True, to='data.MetadataStandard', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='field',
            name='vocabulary',
            field=models.ForeignKey(serialize=False, blank=True, to='data.Vocabulary', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='field',
            unique_together=set([('name', 'standard')]),
        ),
        migrations.AlterOrderWithRespectTo(
            name='field',
            order_with_respect_to='standard',
        ),
        migrations.AddField(
            model_name='collectionitem',
            name='record',
            field=models.ForeignKey(to='data.Record'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='records',
            field=models.ManyToManyField(to='data.Record', through='data.CollectionItem'),
            preserve_default=True,
        ),
    ]
