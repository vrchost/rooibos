# Generated by Django 3.1.14 on 2022-01-19 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0013_auto_20191010_1353'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vocabulary',
            name='standard',
            field=models.BooleanField(null=True),
        ),
    ]