from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from datetime import datetime


class Activity(models.Model):
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()
    event = models.CharField(max_length=64)
    data = models.TextField(blank=True)
    
    def __unicode__(self):
        return "Activity (%s %s) %s" % (self.date, self.time, self.event)
    
    def save(self, *args, **kwargs):
        if not self.date:
            self.date = datetime.now().date()
        if not self.time:
            self.time = datetime.now().time()
        super(Activity, self).save(*args, **kwargs)
    
    
class AccumulatedActivity(models.Model):
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    date = models.DateField()
    event = models.CharField(max_length=64)
    final = models.BooleanField(default=False)
    count = models.IntegerField()

    def __unicode__(self):
        return "AccumulatedActivity (%s) %s %s" % (self.date, self.event, self.count)
