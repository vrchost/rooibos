# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-10-10 13:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0012_add_equivalent_index'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='field',
            options={},
        ),
        migrations.AlterField(
            model_name='field',
            name='equivalent',
            field=models.ManyToManyField(blank=True, related_name='_field_equivalent_+', to='data.Field'),
        ),
    ]
