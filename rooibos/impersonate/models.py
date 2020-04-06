from django.db import models
from django.contrib.auth.models import User, Group


class Impersonation(models.Model):
    group = models.ForeignKey(Group, related_name='impersonating_set')
    users = models.ManyToManyField(User, verbose_name='Allowed users', related_name='impersonated_set', blank=True)
    groups = models.ManyToManyField(Group, verbose_name='Allowed groups', related_name='impersonated_set', blank=True)

    def __str__(self):
        return self.group.name
