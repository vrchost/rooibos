from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rooibos.access import accessible_ids
from rooibos.util import unique_slug, cached_property, clear_cached_properties
import logging
import random


class Collection(models.Model):

    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True, blank=True)
    children = models.ManyToManyField('self', symmetrical=False, blank=True)
    records = models.ManyToManyField('Record', through='CollectionItem')
    owner = models.ForeignKey(User, null=True, blank=True)
    hidden = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    agreement = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ['title']
        
    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Collection, self).save(kwargs)

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.name)

    #def get_absolute_url(self):
    #    return reverse('data-collection', kwargs={'id': self.id, 'name': self.name})

    @property
    def all_child_collections(self):
        sub = list(self.children.all())
        result = ()
        while True:
            todo = ()
            for collection in sub:
                if self != collection:
                    result += (collection,)
                for g in collection.children.all():
                    if g != self and not g in sub:
                        todo += (g,)
            if not todo:
                break
            sub = todo
        return result

    @property
    def all_parent_collections(self):
        parents = list(self.collection_set.all())
        result = ()
        while True:
            todo = ()
            for collection in parents:
                if self != collection:
                    result += (collection,)
                for g in collection.collection_set.all():
                    if g != self and not g in parents:
                        todo += (g,)
            if not todo:
                break
            sub = todo
        return result

    @property
    def all_records(self):
        return Record.objects.filter(collection__in=self.all_child_collections + (self,)).distinct()


class CollectionItem(models.Model):
    collection = models.ForeignKey('Collection')
    record = models.ForeignKey('Record')
    hidden = models.BooleanField(default=False)

    def __unicode__(self):
        return "Record %s Collection %s%s" % (self.record_id, self.collection_id, 'hidden' if self.hidden else '')

class Record(models.Model):
    created = models.DateTimeField(default=datetime.now())
    modified = models.DateTimeField(auto_now=True)
    name = models.SlugField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True)
    source = models.CharField(max_length=1024, null=True)
    manager = models.CharField(max_length=50, null=True)
    next_update = models.DateTimeField(null=True)
    owner = models.ForeignKey(User, null=True)

    @staticmethod
    def get_or_404(id, user):
        if user.is_superuser:
            q = Q()
        else:
            q = ((Q(owner=user) if user.is_authenticated() else Q(owner=None)) |
                 Q(collection__id__in=accessible_ids(user, Collection)))
        return get_object_or_404(Record.objects.filter(q, id=id).distinct())

    @staticmethod
    def by_fieldvalue(fields, values):
        try:
            fields = iter(fields)
        except TypeError:
            fields = [fields]
        if not isinstance(values, (list, tuple)):
            values = [values]
            
        index_values = [value[:32] for value in values]
        
        values_q = reduce(lambda q, value: q | Q(fieldvalue__value__iexact=value), values, Q())
        
        return Record.objects.filter(values_q,
                                     fieldvalue__index_value__in=index_values,
                                     fieldvalue__field__in=fields)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('data-record', kwargs={'id': self.id, 'name': self.name})

    def get_thumbnail_url(self):
        return reverse('storage-thumbnail', kwargs={'id': self.id, 'name': self.name})

    def get_image_url(self):
        return reverse('storage-retrieve-image-nosize', kwargs={'recordid': self.id, 'record': self.name})

    def save(self, force_update_name=False, **kwargs):
        unique_slug(self, slug_literal='r-%s' % random.randint(1000000, 9999999),
                    slug_field='name', check_current_slug=kwargs.get('force_insert') or force_update_name)
        self._clear_cached_items()
        super(Record, self).save(kwargs)

    def get_fieldvalues(self, owner=None, context=None, fieldset=None, hidden=False, include_context_owner=False,
                        hide_default_data=False, q=None):
        qc = Q(context_type=None, context_id=None)
        if context:
            qc = qc | Q(context_type=ContentType.objects.get_for_model(context.__class__), context_id=context.id)
        qo = Q(owner=None) if not hide_default_data else Q()
        if owner and owner.is_authenticated():
            qo = qo | Q(owner=owner)
        if context and include_context_owner and hasattr(context, 'owner') and context.owner:
            qo = qo | Q(owner=context.owner)
        qh = Q() if hidden else Q(hidden=False)

        q = q or Q()

        values = self.fieldvalue_set.select_related('record', 'field').filter(qc, qo, qh, q) \
                    .order_by('order','field','group','refinement')

        if fieldset:
            values_to_map = []
            result = {}
            eq_cache = {}
            target_fields = fieldset.fields.all().order_by('fieldsetfield__order')

            for v in values:
                if v.field in target_fields:
                    result.setdefault(v.field, []).append(DisplayFieldValue.from_value(v, v.field))
                else:
                    values_to_map.append(v)

            for v in values_to_map:
                eq = eq_cache.has_key(v.field) and eq_cache[v.field] or eq_cache.setdefault(v.field, v.field.get_equivalent_fields())
                for f in eq:
                    if f in target_fields:
                        result.setdefault(f, []).append(DisplayFieldValue.from_value(v, f))
                        break

            values = []
            for f in target_fields:
                values.extend(sorted(result.get(f, [])))

        return values

    def dump(self, owner=None, collection=None):
        print("Created: %s" % self.created)
        print("Modified: %s" % self.modified)
        print("Name: %s" % self.name)
        for v in self.fieldvalue_set.all():
            v.dump(owner, collection)

    @property
    def title(self):
        if not getattr(self, "_cached_title", None):
            titlefield = Field.objects.get(standard__prefix='dc', name='title')
            titles = self.fieldvalue_set.filter(
                Q(field=titlefield) | Q(field__in=titlefield.get_equivalent_fields()),
                owner=None,
                context_type=None,
                hidden=False)
            self._cached_title = None if not titles else titles[0].value
        return self._cached_title

    @property
    def shared(self):
        return bool(self.collectionitem_set.filter(hidden=False).count()) if self.owner else None

    def _clear_cached_items(self):
        clear_cached_properties(self, 'title', 'thumbnail')

    

class MetadataStandard(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    prefix = models.CharField(max_length=16, unique=True)

    def __unicode__(self):
        return self.title


class Vocabulary(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    description = models.TextField(null=True, blank=True)
    standard = models.NullBooleanField()
    origin = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "vocabularies"

    
class VocabularyTerm(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    term = models.TextField()


class Field(models.Model):
    label = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    old_name = models.CharField(max_length=100, null=True, blank=True)
    standard = models.ForeignKey(MetadataStandard, null=True, blank=True)
    equivalent = models.ManyToManyField("self", null=True, blank=True)
    vocabulary = models.ForeignKey(Vocabulary, null=True, blank=True)

    def save(self, **kwargs):
        unique_slug(self, slug_source='label', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Field, self).save(kwargs)

    @property
    def full_name(self):
        if self.standard:
            return "%s.%s" % (self.standard.prefix, self.name)
        else:
            return self.name

    def get_equivalent_fields(self):
        ids = list(self.equivalent.values_list('id', flat=True))
        more = len(ids) > 1
        while more:
            more = Field.objects.filter(~Q(id__in=ids), ~Q(standard=self.standard), equivalent__id__in=ids).values_list('id', flat=True)
            ids.extend(more)
        return Field.objects.select_related('standard').filter(id__in=ids)

    def __unicode__(self):
        return self.full_name

    class Meta:
        unique_together = ('name', 'standard')
        ordering = ['name']
        order_with_respect_to = 'standard'
        

def get_system_field():
    field, created = Field.objects.get_or_create(name='system-value',
                                                 defaults=dict(label='System Value'))
    return field


class FieldSet(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    fields = models.ManyToManyField(Field, through='FieldSetField')
    owner = models.ForeignKey(User, null=True, blank=True)
    standard = models.BooleanField(default=False)

    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(FieldSet, self).save(kwargs)

    def __unicode__(self):
        return self.title
    
    class Meta:
        ordering = ['title']
        
    @staticmethod
    def for_user(user):
        return FieldSet.objects.filter(Q(owner=None) | Q(standard=True) |
                                        (Q(owner=user) if user.is_authenticated() else Q()))


class FieldSetField(models.Model):
    fieldset = models.ForeignKey(FieldSet)
    field = models.ForeignKey(Field)
    label = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    importance = models.SmallIntegerField(default=1)

    def __unicode__(self):
        return self.field.__unicode__()

    class Meta:
        ordering = ['order']


class FieldValue(models.Model):
    record = models.ForeignKey(Record, editable=False)
    field = models.ForeignKey(Field)
    refinement = models.CharField(max_length=100, null=True, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True)
    label = models.CharField(max_length=100, null=True, blank=True)
    hidden = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    group = models.IntegerField(null=True, blank=True)
    value = models.TextField()
    index_value = models.CharField(max_length=32, db_index=True)
    date_start = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=0)
    date_end = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=0)
    numeric_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    language = models.CharField(max_length=5, null=True, blank=True)
    context_type = models.ForeignKey(ContentType, null=True, blank=True)
    context_id = models.PositiveIntegerField(null=True, blank=True)
    context = generic.GenericForeignKey('context_type', 'context_id')

    def save(self, **kwargs):
        self.index_value = self.value[:32] if self.value != None else None
        super(FieldValue, self).save(kwargs)
        
    def __unicode__(self):
        return "%s%s%s=%s" % (self.resolved_label, self.refinement and '.', self.refinement, self.value)

    @property
    def resolved_label(self):
        return self.label or self.field.label

    def dump(self, owner=None, collection=None):
        print("%s: %s" % (self.resolved_label, self.value))
        
    class Meta:
        ordering = ['order']


class DisplayFieldValue(FieldValue):
    """
    Represents a mapped field value for display.  Cannot be saved.
    """
    def save(self, *args, **kwargs):
        raise NotImplementedError()

    def __cmp__(self, other):
        order_by = ('_original_field_name', 'group', 'order', 'refinement')
        for ob in order_by:
            s = getattr(self, ob)
            o = getattr(other, ob)
            if s <> o: return cmp(s, o)
        return 0

    @staticmethod
    def from_value(value, field):
        dfv = DisplayFieldValue(record=value.record,
                                 field=field,
                                 refinement=value.refinement,
                                 owner=value.owner,
                                 hidden=value.hidden,
                                 order=value.order,
                                 group=value.group,
                                 value=value.value,
                                 index_value=value.index_value,
                                 date_start=value.date_start,
                                 date_end=value.date_end,
                                 numeric_value=value.numeric_value,
                                 language=value.language,
                                 context_type=value.context_type,
                                 context_id=value.context_id)
        dfv._original_field_name = value.field.name
        return dfv


def standardfield(field, standard='dc', equiv=False):
    f = Field.objects.get(standard__prefix=standard, name=field)
    if equiv:
        return Field.objects.filter(Q(id=f.id) | Q(id__in=f.get_equivalent_fields()))
    else:
        return f
