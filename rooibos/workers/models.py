from django.db import models
from django.contrib.auth.models import User
from django_celery_results.models import TaskResult


class OwnedTaskResult(TaskResult):

    owner = models.ForeignKey(User, null=False, blank=False)
    function = models.CharField(max_length=64)
    args = models.TextField(null=True, default=None, editable=False)
    created = models.DateTimeField(auto_now=True)

    def as_dict(self):
        result = super(OwnedTaskResult, self).as_dict()
        result['owner'] = self.owner.username if self.owner else None
        return result
