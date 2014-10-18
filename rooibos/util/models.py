from django.db import models, IntegrityError, transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group


# Using race condition fix for get_or_created suggested on
# https://stackoverflow.com/questions/2235318
@transaction.commit_on_success
class OwnedWrapperManager(models.Manager):
    """
    Allows retrieval of a wrapper object by specifying
    """
    def get_for_object(self, user, object=None, type=None, object_id=None):
        try:
            type = int(type)
        except TypeError:
            pass

        try:
            obj, created = self.get_or_create(
                user=user,
                object_id=object and object.id or object_id,
                content_type=object and OwnedWrapper.t(object.__class__) or type)
        except IntegrityError:
            transaction.commit()
            obj = self.get(
                user=user,
                object_id=object and object.id or object_id,
                content_type=object and OwnedWrapper.t(object.__class__) or type)
        return obj


class OwnedWrapper(models.Model):
    """
    Used to connect a user to an object, currently used for tagging purposes to
    keep track of tag owners
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User)
    taggeditem = generic.GenericRelation('tagging.TaggedItem')

    objects = OwnedWrapperManager()

    class Meta:
        unique_together = ('content_type', 'object_id', 'user')

    @staticmethod
    def t(model):
        return ContentType.objects.get_for_model(model)
