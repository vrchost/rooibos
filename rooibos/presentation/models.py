from django.db import models, connection
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.fields import GenericRelation
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from rooibos.data.models import Record, FieldSet, FieldValue, standardfield, \
    standardfield_ids
from rooibos.storage.models import Media
from rooibos.util import unique_slug
from rooibos.access.functions import filter_by_access
from functools import reduce


class Presentation(models.Model):

    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    owner = models.ForeignKey(User)
    hidden = models.BooleanField(default=False)
    source = models.CharField(max_length=1024, null=True)
    description = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)
    fieldset = models.ForeignKey(FieldSet, null=True)
    hide_default_data = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    ownedwrapper = GenericRelation('util.OwnedWrapper')

    def save(self, **kwargs):
        unique_slug(
            self,
            slug_source='title',
            slug_field='name',
            check_current_slug=kwargs.get('force_insert')
        )
        super(Presentation, self).save(kwargs)

    def get_absolute_url(self):
        return reverse(
            'presentation-edit',
            kwargs={
                'id': self.id,
                'name': self.name
            }
        )

    def override_dates(self, created=None, modified=None):
        cursor = connection.cursor()
        if created and self.id:
            cursor.execute(
                "UPDATE %s SET created=%%s WHERE id=%%s" %
                self._meta.db_table, [created, self.id]
            )
        if modified and self.id:
            cursor.execute(
                "UPDATE %s SET modified=%%s WHERE id=%%s" %
                self._meta.db_table, [modified, self.id]
            )

    def cached_items(self):
        if not hasattr(self, '_cached_items'):
            self._cached_items = tuple(self.items.all())
        return self._cached_items

    def records(self):
        return [i.record for i in self.items.all()]

    def visible_item_count(self):
        return len([i for i in self.cached_items() if not i.hidden])

    def hidden_item_count(self):
        return len([i for i in self.cached_items() if i.hidden])

    def duplicate(self):
        dup = Presentation()
        dup.title = self.title
        dup.owner = self.owner
        dup.hidden = self.hidden
        dup.description = self.description
        dup.password = self.password
        dup.fieldset = self.fieldset
        dup.hide_default_data = self.hide_default_data
        return dup

    @staticmethod
    def check_passwords(passwords):
        if passwords:
            q = reduce(
                lambda a, b: a | b,
                (
                    Q(id=id, password=password)
                    for id, password in passwords.items()
                )
            )
            return Presentation.objects.filter(q).values_list('id', flat=True)
        else:
            return []

    def verify_password(self, request):
        self.unlocked = (
            (self.owner == request.user) or
            (not self.password) or
            (request.session.get('passwords', dict()).get(self.id) ==
             self.password)
        )
        return self.unlocked

    @staticmethod
    def published_q(owner=None):
        publish_permission = Permission.objects.get(
            codename='publish_presentations')
        valid_publishers = User.objects.filter(
            Q(id__in=publish_permission.user_set.all()) |
            Q(groups__id__in=publish_permission.group_set.all()) |
            Q(is_superuser=True)
        )
        q = Q(owner__in=valid_publishers) & Q(hidden=False)
        if owner and not owner.is_anonymous():
            return q | Q(id__in=filter_by_access(
                owner, Presentation, manage=True))
        else:
            return q

    @staticmethod
    def get_by_id_for_request(id, request):
        p = (filter_by_access(request.user, Presentation)
             .filter(Presentation.published_q(request.user), id=id))
        return p[0] if p and p[0].verify_password(request) else None

    class Meta:
        permissions = (
            ("publish_presentations", "Can publish presentations"),
        )


class PresentationItem(models.Model):

    presentation = models.ForeignKey('Presentation', related_name='items')
    record = models.ForeignKey(Record)
    hidden = models.BooleanField(default=False)
    type = models.CharField(max_length=16, blank=True)
    order = models.SmallIntegerField()

    def title_from_fieldvalues(self, fieldvalues):
        titlefields = standardfield_ids('title', equiv=True)
        for fv in fieldvalues:
            if fv.field_id in titlefields:
                return fv.value
        return None

    @property
    def title(self):
        return self.title_from_fieldvalues(self.get_fieldvalues())

    def _annotation_filter(self):
        return dict(
            owner=self.presentation.owner,
            context_id=self.id,
            context_type=ContentType.objects.get_for_model(PresentationItem),
            field=standardfield('description'),
            record=self.record
        )

    def annotation_getter(self):
        if self.id:
            try:
                return FieldValue.objects.get(
                    **self._annotation_filter()).value
            except FieldValue.DoesNotExist:
                return None
        elif hasattr(self, '_saved_annotation'):
            return self._saved_annotation
        else:
            return None

    def annotation_setter(self, value):
        if self.id:
            if value:
                fv, created = FieldValue.objects.get_or_create(
                    defaults=dict(label='Annotation',
                                  value=value),
                    **self._annotation_filter()
                )
                if not created:
                    fv.value = value
                    fv.save()
            else:
                try:
                    FieldValue.objects.get(
                        **self._annotation_filter()).delete()
                except FieldValue.DoesNotExist:
                    pass
        else:
            # we are not saved yet, so remember annotation for later
            self._saved_annotation = value

    annotation = property(annotation_getter, annotation_setter)

    def save(self, *args, **kwargs):
        super(PresentationItem, self).save(*args, **kwargs)
        if hasattr(self, '_saved_annotation'):
            self.annotation = self._saved_annotation

    def duplicate(self):
        dup = PresentationItem()
        dup.record = self.record
        dup.hidden = self.hidden
        dup.type = self.type
        dup.order = self.order
        dup.annotation = self.annotation
        return dup

    def get_fieldvalues(self, owner=None, hidden=False,
                        include_context_owner=True, q=None):
        return self.record.get_fieldvalues(
            owner=owner,
            context=self.presentation,
            fieldset=self.presentation.fieldset,
            hidden=hidden,
            include_context_owner=include_context_owner,
            hide_default_data=self.presentation.hide_default_data,
            q=q
        )

    class Meta:
        ordering = ['order']


class PresentationItemInfo(models.Model):

    item = models.ForeignKey('PresentationItem', related_name='media')
    media = models.ForeignKey(Media)
    info = models.TextField(blank=True)
