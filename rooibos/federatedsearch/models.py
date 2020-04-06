from django.db import models
from datetime import datetime


class CurrentHitCountManager(models.Manager):
    def get_queryset(self):
        return super(CurrentHitCountManager, self).get_queryset().filter(
            valid_until__gt=datetime.now())


class HitCount(models.Model):

    query = models.CharField(max_length=255, db_index=True)
    source = models.CharField(max_length=32, db_index=True)
    hits = models.IntegerField()
    results = models.TextField(blank=True, null=True)
    valid_until = models.DateTimeField()

    objects = models.Manager()
    current_objects = CurrentHitCountManager()

    def __str__(self):
        return "%s '%s': %s" % (self.source, self.query, self.hits)
