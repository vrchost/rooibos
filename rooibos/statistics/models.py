from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
from datetime import datetime


class Activity(models.Model):
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    user_field = models.ForeignKey(
        User, null=True, blank=True, db_column='user_id')
    date = models.DateField(db_index=True)
    time = models.TimeField()
    event = models.CharField(max_length=64, db_index=True)
    data_field = models.TextField(blank=True, db_column='data')

    class Meta:
        app_label = 'statistics'

    def __str__(self):
        return "Activity (%s %s) %s" % (self.date, self.time, self.event)

    # Override user property to allow AnonymousUser objects,
    # which otherwise fail
    def _user_get(self):
        return self.user_field

    def _user_set(self, value):
        self.user_field = value if value and not value.is_anonymous() else None
    user = property(_user_get, _user_set)

    # Override data property to take a dict() object
    def _data_get(self):
        if self.data_field:
            return eval(self.data_field, {"__builtins__": None}, {})
        else:
            return None

    def _data_set(self, value):
        if not value:
            self.data_field = ''
        elif type(value) == dict:
            self.data_field = repr(value)
        else:
            self.data_field = repr(dict(data=value))
    data = property(_data_get, _data_set)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request') if 'request' in kwargs else None
        super(Activity, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = datetime.now().date()
        if not self.time:
            self.time = datetime.now().time()
        if not self.data:
            self.data = ''
        if self.request:
            self.user = self.request.user
            r = {'request.referer': self.request.META.get('HTTP_REFERER'),
                 'request.remote_addr': self.request.META.get('REMOTE_ADDR')}
            if self.data:
                r.update(self.data)
            self.data = r
        super(Activity, self).save(*args, **kwargs)


class AccumulatedActivity(models.Model):
    content_type = models.ForeignKey(ContentType, null=True)
    object_id = models.PositiveIntegerField(null=True, db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    date = models.DateField(db_index=True)
    event = models.CharField(max_length=64, db_index=True)
    final = models.BooleanField(default=False)
    count = models.IntegerField()

    class Meta:
        app_label = 'statistics'

    def __str__(self):
        return "AccumulatedActivity (%s) %s %s" % (
            self.date, self.event, self.count)
