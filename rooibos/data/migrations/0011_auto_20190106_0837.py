# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0010_remove_dc_vra_equivalent_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='password',
            field=models.CharField(max_length=32, serialize=False, blank=True),
        ),
    ]
