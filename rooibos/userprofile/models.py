from django.db import models
from django.contrib.auth.models import User


class Preference(models.Model):
    setting = models.CharField(max_length=128)
    value = models.TextField()

    def __unicode__(self):
        return "%s=%s" % (self.setting, self.value)
    

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    preferences = models.ManyToManyField(Preference)

    def __unicode__(self):
        return "%s" % self.user