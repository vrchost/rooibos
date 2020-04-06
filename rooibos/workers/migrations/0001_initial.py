# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnedTaskResult',
            fields=[
                ('taskresult_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='django_celery_results.TaskResult')),
                ('function', models.CharField(max_length=64)),
                ('args', models.TextField(default=None, null=True, editable=False)),
                ('created', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            bases=('django_celery_results.taskresult',),
        ),
    ]
