from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import hashlib


class ObjectHistory(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey(
        'content_type', 'object_id')
    m2m_content_type = models.ForeignKey(
        ContentType, null=True, related_name='m2m_objecthistory_set')
    m2m_object_id = models.PositiveIntegerField(null=True)
    m2m_content_object = GenericForeignKey(
        'm2m_content_type', 'm2m_object_id')
    type = models.CharField(max_length=8, null=True, db_index=True)
    original_id = models.CharField(max_length=255, db_index=True)
    content_hash = models.CharField(max_length=32)


def content_hash(*args):
    hash = hashlib.md5()
    for arg in args:
        hash.update(repr(arg))
    return hash.hexdigest()
