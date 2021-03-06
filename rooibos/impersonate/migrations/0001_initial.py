# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-10-10 13:53
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Impersonation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impersonating_set', to='auth.Group')),
                ('groups', models.ManyToManyField(blank=True, related_name='impersonated_set', to='auth.Group', verbose_name='Allowed groups')),
                ('users', models.ManyToManyField(blank=True, related_name='impersonated_set', to=settings.AUTH_USER_MODEL, verbose_name='Allowed users')),
            ],
        ),
    ]
