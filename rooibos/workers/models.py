from django.db import models
from django.contrib.auth.models import User
from django_celery_results.models import TaskResult


class TaskOwnership(models.Model):
    task = models.OneToOneField(
        TaskResult,
        to_field='task_id',
        db_constraint=False,
        null=False,
        blank=False,
    )
    owner = models.ForeignKey(User, null=False, blank=False)

    def __str__(self):
        return '<TaskResult: {0.task} ({0.owner})>'.format(self)
