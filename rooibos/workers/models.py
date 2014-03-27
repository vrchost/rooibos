from django.db import models
from django.contrib.auth.models import User
from registration import run_worker
from datetime import datetime, timedelta


class JobInfo(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True)
    func = models.CharField(max_length=128)
    arg = models.TextField()
    status = models.TextField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)
    status_time = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    result = models.TextField()

    class Meta:
        ordering = ['completed', '-created_time']

    def run(self):
        try:
            self.status = 'Starting'
            self.save()
            return run_worker(self.func, self.id, background=True)
        except Exception, ex:
            self.status = 'Start failed. %s' % ex
            self.save()

    def update_status(self, status):
        self.status = status
        self.status_time = datetime.now()
        self.save()

    def complete(self, status, result):
        self.result = result or "-"
        self.completed = True
        self.update_status(status)

    def stalled(self):
        return (not self.completed
                and self.status_time
                and (datetime.now() - self.status_time > timedelta(0, 60)))
