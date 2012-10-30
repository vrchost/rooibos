from django.db import models
from datetime import datetime


class CurrentHitCountManager(models.Manager):
    def get_query_set(self):
        return super(CurrentHitCountManager, self).get_query_set().filter(valid_until__gt=datetime.now())


class HitCount(models.Model):

    query = models.CharField(max_length=255, db_index=True)
    source = models.CharField(max_length=32, db_index=True)
    hits = models.IntegerField()
    results = models.TextField(blank=True, null=True)
    valid_until = models.DateTimeField()

    objects = models.Manager()
    current_objects = CurrentHitCountManager()

    def __unicode__(self):
        return "%s '%s': %s" % (self.source, self.query, self.hits)


class FederatedSearch(object):

    def __init__(self, timeout=10):
        super(FederatedSearch, self).__init__()
        self.timeout = timeout

    def hits_count(self, query):
        raise NotImplementedError

    def get_label(self):
        raise NotImplementedError

    def get_source_id(self):
        raise NotImplementedError

    def get_search_url(self):
        raise NotImplementedError
