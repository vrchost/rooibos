from django.db import models
from django.contrib.auth.models import User


class Preference(models.Model):
    setting = models.CharField(max_length=128)
    value = models.TextField()

    def __str__(self):
        return "%s=%s" % (self.setting, self.value)


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    preferences = models.ManyToManyField(Preference, blank=True)

    def __str__(self):
        return "%s" % self.user
