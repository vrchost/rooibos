from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import Q, signals
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rooibos.access.functions import filter_by_access, check_access
from rooibos.access.models import AccessControl
from rooibos.util import unique_slug
import random
import types
import re
import unicodedata
from functools import reduce, total_ordering


class CollectionManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Collection(models.Model):
    objects = CollectionManager()

    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True, blank=True)
    children = models.ManyToManyField(
        'self', symmetrical=False, blank=True, serialize=False)
    records = models.ManyToManyField('Record', through='CollectionItem')
    owner = models.ForeignKey(User, null=True, blank=True, serialize=False)
    hidden = models.BooleanField(default=False, serialize=False)
    description = models.TextField(blank=True)
    agreement = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, serialize=False)
    order = models.IntegerField(blank=False, null=False, default=100)

    def natural_key(self):
        return (self.name,)

    class Meta:
        ordering = ['order', 'title']
        app_label = 'data'

    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name',
                    check_current_slug=kwargs.get('force_insert'))
        super(Collection, self).save(kwargs)

    def __str__(self):
        return '%s (%s)' % (self.title, self.name)

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
                    if g != self and g not in sub:
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
                    if g != self and g not in parents:
                        todo += (g,)
            if not todo:
                break
            parents = todo
        return result

    @property
    def all_records(self):
        return Record.objects.filter(
            collection__in=self.all_child_collections + (self,)).distinct()


class CollectionItemManager(models.Manager):
    def get_by_natural_key(self, collection_name, record_name):
        return self.get(
            collection__name=collection_name, record__name=record_name)


class CollectionItem(models.Model):
    objects = CollectionItemManager()

    collection = models.ForeignKey('Collection')
    record = models.ForeignKey('Record')
    hidden = models.BooleanField(default=False)

    def natural_key(self):
        return self.collection.natural_key() + self.record.natural_key()

    natural_key.dependencies = ['data.Collection', 'data.Record']

    def __str__(self):
        return "Record %s Collection %s%s" % (
            self.record_id,
            self.collection_id,
            'hidden' if self.hidden else ''
        )

    class Meta:
        app_label = 'data'


def _records_with_individual_acl_by_ids(ids):
    return list(AccessControl.objects.filter(
        content_type=ContentType.objects.get_for_model(Record),
        object_id__in=ids).values_list('object_id', flat=True))


class RecordManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Record(models.Model):
    objects = RecordManager()

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.SlugField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True)
    source = models.CharField(max_length=1024, null=True, blank=True)
    manager = models.CharField(max_length=50, null=True, blank=True)
    next_update = models.DateTimeField(null=True, blank=True, serialize=False)
    owner = models.ForeignKey(User, null=True, blank=True, serialize=False)

    class Meta:
        app_label = 'data'

    def natural_key(self):
        return (self.name,)

    @staticmethod
    def filter_by_access(user, *ids):
        records = Record.objects.distinct()

        ids = list(map(int, ids))

        if user and user.is_superuser:
            return records.filter(id__in=ids)

        allowed_ids = []
        to_check = ids

        # check which records have individual ACLs set
        individual = _records_with_individual_acl_by_ids(to_check)
        if individual:
            allowed_ids.extend(
                filter_by_access(
                    user,
                    Record.objects.filter(id__in=individual)
                ).values_list('id', flat=True)
            )
            to_check = [id for id in to_check if id not in individual]
        # check records without individual ACLs
        if to_check:
            readable = filter_by_access(user, Collection)
            writable = filter_by_access(user, Collection, write=True)
            cq = Q(collectionitem__collection__in=readable,
                   collectionitem__hidden=False)
            mq = Q(collectionitem__collection__in=writable,
                   owner=None)
            oq = Q(owner=user) if user and not user.is_anonymous() else Q()
            records = records.filter(cq | mq | oq)
            checked = records.filter(
                id__in=to_check).values_list('id', flat=True)
            allowed_ids.extend(checked)

        return records.filter(id__in=allowed_ids)

    @staticmethod
    def filter_one_by_access(user, id):
        try:
            return Record.filter_by_access(user, id).get()
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_or_404(id, user):
        return get_object_or_404(Record.filter_by_access(user, id))

    @staticmethod
    def by_fieldvalue(fields, values):
        try:
            fields = iter(fields)
        except TypeError:
            fields = [fields]
        if not isinstance(values, (list, tuple, types.GeneratorType)):
            values = [values]

        index_values = [value[:32] for value in values]

        values_q = reduce(
            lambda q, value: q | Q(fieldvalue__value__iexact=value),
            values,
            Q()
        )

        return Record.objects.filter(values_q,
                                     fieldvalue__index_value__in=index_values,
                                     fieldvalue__field__in=fields)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            'data-record', kwargs={'id': self.id, 'name': self.name})

    def _get_thumbnail_url(self, fmt, force_cdn=False):
        cdn_thumbnails = getattr(settings, 'CDN_THUMBNAILS', None)
        if cdn_thumbnails:
            for collection_name in self.collection_set.values_list(
                    'name', flat=True):
                for key in cdn_thumbnails:
                    m = re.match(key, collection_name)
                    if m and m.end() == len(collection_name):
                        if fmt in cdn_thumbnails[key]:
                            return cdn_thumbnails[key][fmt] % self.identifier
        if force_cdn:
            return None
        url = reverse(
            'storage-thumbnail', kwargs={'id': self.id, 'name': self.name})
        if fmt == 'square':
            url += '?square'
        return url

    def get_thumbnail_url(self, format='regular', force_cdn=False):
        return self._get_thumbnail_url(format, force_cdn)

    def get_square_thumbnail_url(self):
        return self._get_thumbnail_url('square')

    def get_image_url(self, force_reprocess=False, width=None, height=None,
                      handler=None):
        if width and height:
            url = reverse(
                handler or 'storage-retrieve-image',
                kwargs={
                    'recordid': self.id,
                    'record': self.name,
                    'width': width,
                    'height': height,
                }
            )
        else:
            url = reverse(
                handler or 'storage-retrieve-image-nosize',
                kwargs={
                    'recordid': self.id,
                    'record': self.name
                }
            )
        if force_reprocess:
            url += '?reprocess'
        return url

    def save(self, force_update_name=False, **kwargs):
        # TODO: update this to use something human readable and/or
        # globally unique
        unique_slug(
            self,
            slug_literal='r-%s' % random.randint(1000000, 9999999),
            slug_field='name',
            check_current_slug=kwargs.get('force_insert') or force_update_name
        )
        super(Record, self).save(kwargs)

    def get_fieldvalues(self, owner=None, context=None, fieldset=None,
                        hidden=False, include_context_owner=False,
                        hide_default_data=False, q=None):
        qc = Q(context_type=None, context_id=None)
        if context:
            contenttype = ContentType.objects.get_for_model(context.__class__)
            qc = qc | Q(context_type=contenttype, context_id=context.id)
        qo = Q(owner=None) if not hide_default_data else Q()
        if owner and owner.is_authenticated():
            qo = qo | Q(owner=owner)
        if context and include_context_owner and hasattr(context, 'owner') \
                and context.owner:
            qo = qo | Q(owner=context.owner)
        qh = Q() if hidden else Q(hidden=False)

        q = q or Q()

        values = self.fieldvalue_set \
            .select_related('record', 'field').filter(qc, qo, qh, q) \
            .order_by('order', 'field', 'group', 'refinement')

        if fieldset:
            values_to_map = []
            result = {}
            eq_cache = {}
            target_fields = fieldset.fields.all().order_by(
                'fieldsetfield__order')

            for v in values:
                if v.field in target_fields:
                    result.setdefault(v.field, []).append(
                        DisplayFieldValue.from_value(v, v.field))
                else:
                    values_to_map.append(v)

            for v in values_to_map:
                eq = (
                    eq_cache[v.field]
                    if v.field in eq_cache
                    else eq_cache.setdefault(
                        v.field, v.field.get_equivalent_fields())
                )
                for f in eq:
                    if f in target_fields:
                        result.setdefault(f, []).append(
                            DisplayFieldValue.from_value(v, f))
                        break

            values = []
            for f in target_fields:
                values.extend(sorted(result.get(f, [])))

        for i in range(0, len(values)):
            values[i].subitem = (
                i > 0 and
                values[i].field == values[i - 1].field and
                values[i].group == values[i - 1].group and
                values[i].resolved_label ==
                values[i - 1].resolved_label
            )

        return values

    def dump(self, owner=None, collection=None):
        print(("Created: %s" % self.created))
        print(("Modified: %s" % self.modified))
        print(("Name: %s" % self.name))
        for v in self.fieldvalue_set.all():
            v.dump(owner, collection)

    def _get_field_value(self, field_name, hidden=False, standard='dc'):
        fields = standardfield_ids(field_name, equiv=True, standard=standard)
        values = self.fieldvalue_set.filter(
            field__in=fields,
            owner=None,
            context_type=None)
        if hidden is not None:
            values = values.filter(hidden=hidden)
        return values[0].value if values else None

    @property
    def title(self):
        return self._get_field_value('title') if self.id else None

    @property
    def identifier(self):
        return self._get_field_value('identifier') if self.id else None

    @property
    def work_title(self):
        work_title = self._get_field_value(
            'title', standard='vra') if self.id else None
        return work_title or self.title

    @property
    def alt_text(self):
        return (
            self._get_field_value('alt-text', standard='system', hidden=None)
            or self.title
        ) if self.id else None

    @property
    def shared(self):
        if self.owner:
            return bool(self.collectionitem_set.filter(hidden=False).count())
        else:
            return None

    def _check_permission_for_user(self, user, **permissions):
        # checks if user is owner or has ACL access
        if check_access(user, self, **permissions):
            return True
        # if record does not have individual ACL...
        if len(_records_with_individual_acl_by_ids([self.id])) > 0:
            return False
        # ...check collection access
        return filter_by_access(
            user, self.collection_set, **permissions).count() > 0

    def editable_by(self, user):
        return self._check_permission_for_user(user, write=True)

    def manageable_by(self, user):
        return self._check_permission_for_user(user, manage=True)

    def get_works(self):
        values = self.fieldvalue_set.filter(
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
        ).values_list('value', flat=True)
        return values

    def get_image_records_query(self):

        values = self.fieldvalue_set.filter(
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
        ).values_list('value', flat=True)
        index_values = [
            value[:32] for value in values
        ]

        q = Q(value__in=values, index_value__in=index_values)
        return FieldValue.objects.filter(
            q,
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
        ).values('record')

    @staticmethod
    def get_primary_work_record(work):
        record_ids = FieldValue.objects.filter(
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
            value=work,
            index_value=work[:32],
        ).order_by('record').values_list('record', flat=True)

        if not record_ids:
            return None

        primary = FieldValue.objects.filter(
            label='primary-work-record',
            field__standard__prefix='dc',
            field__name='system-value',
            record__in=record_ids,
        ).order_by('record').values_list('record', flat=True)

        if primary:
            primary = primary[0]
        else:
            primary = record_ids[0]

        return Record.objects.get(id=primary)


class MetadataStandardManager(models.Manager):
    def get_by_natural_key(self, prefix):
        return self.get(prefix=prefix)


class MetadataStandard(models.Model):
    objects = MetadataStandardManager()

    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    prefix = models.CharField(max_length=16, unique=True)

    class Meta:
        app_label = 'data'

    def natural_key(self):
        return (self.prefix,)

    def __str__(self):
        return self.title


class Vocabulary(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    description = models.TextField(null=True, blank=True)
    standard = models.NullBooleanField()
    origin = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "vocabularies"
        app_label = 'data'


class VocabularyTerm(models.Model):
    vocabulary = models.ForeignKey(Vocabulary)
    term = models.TextField()

    class Meta:
        app_label = 'data'

    def __str__(self):
        return self.term


class FieldManager(models.Manager):
    def get_by_natural_key(self, standard, name):
        q = Q(standard__prefix=standard) if standard else Q(standard=None)
        return self.get(q, name=name)


class Field(models.Model):
    objects = FieldManager()

    label = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    old_name = models.CharField(
        max_length=100, null=True, blank=True, serialize=False)
    standard = models.ForeignKey(MetadataStandard, null=True, blank=True)
    equivalent = models.ManyToManyField("self", blank=True)
    # TODO: serialize vocabularies
    vocabulary = models.ForeignKey(
        Vocabulary, null=True, blank=True, serialize=False)

    def natural_key(self):
        return (self.standard.prefix if self.standard else '', self.name,)

    natural_key.dependencies = ['data.MetadataStandard']

    def save(self, **kwargs):
        unique_slug(
            self,
            slug_source='label',
            slug_field='name',
            check_current_slug=kwargs.get('force_insert')
        )
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
            more = Field.objects.filter(
                ~Q(id__in=ids),
                ~Q(standard=self.standard),
                equivalent__id__in=ids
            ).values_list('id', flat=True)
            ids.extend(more)
        return Field.objects.select_related('standard').filter(id__in=ids)

    def __str__(self):
        return '%s [%s]' % (self.full_name, self.id)

    class Meta:
        unique_together = ('name', 'standard')
        order_with_respect_to = 'standard'
        app_label = 'data'


@transaction.atomic
def get_system_field():
    field, created = Field.objects.get_or_create(
        name='system-value',
        defaults=dict(label='System Value')
    )
    return field


class FieldSet(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    fields = models.ManyToManyField(Field, through='FieldSetField')
    owner = models.ForeignKey(User, null=True, blank=True)
    standard = models.BooleanField(default=False)

    def save(self, **kwargs):
        unique_slug(
            self,
            slug_source='title',
            slug_field='name',
            check_current_slug=kwargs.get('force_insert')
        )
        super(FieldSet, self).save(kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        app_label = 'data'

    @staticmethod
    def for_user(user):
        return FieldSet.objects.filter(
            Q(owner=None) |
            Q(standard=True) |
            (Q(owner=user) if user and user.is_authenticated() else Q())
        )


class FieldSetField(models.Model):
    fieldset = models.ForeignKey(FieldSet)
    field = models.ForeignKey(Field)
    label = models.CharField(max_length=100, null=True, blank=True)
    order = models.IntegerField(default=0)
    importance = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.field.__str__()

    class Meta:
        ordering = ['order']
        app_label = 'data'


class FieldValue(models.Model):
    record = models.ForeignKey(Record, editable=False)
    field = models.ForeignKey(Field)
    refinement = models.CharField(max_length=100, null=True, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True, serialize=False)
    label = models.CharField(max_length=100, null=True, blank=True)
    hidden = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    group = models.IntegerField(null=True, blank=True)
    value = models.TextField()
    index_value = models.CharField(
        max_length=32, db_index=True, serialize=False)
    browse_value = models.CharField(
        max_length=32, db_index=True, serialize=False)
    date_start = models.DecimalField(
        null=True, blank=True, max_digits=12, decimal_places=0)
    date_end = models.DecimalField(
        null=True, blank=True, max_digits=12, decimal_places=0)
    numeric_value = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True)
    language = models.CharField(max_length=5, null=True, blank=True)
    context_type = models.ForeignKey(
        ContentType, null=True, blank=True, serialize=False)
    context_id = models.PositiveIntegerField(
        null=True, blank=True, serialize=False)
    context = GenericForeignKey('context_type', 'context_id')

    def save(self, **kwargs):
        self.index_value = self.value[:32] if self.value is not None else None
        self.browse_value = FieldValue.make_browse_value(self.value) \
            if self.value is not None else None
        super(FieldValue, self).save(kwargs)
        if self.value and self.field.id in standardfield_ids(
                'identifier', equiv=True):
            # update record slug name
            self.record.name = self.value
            self.record.save(force_update_name=True)

    def __str__(self):
        return "%s%s%s=%s" % (
            self.resolved_label,
            self.refinement and '.',
            self.refinement,
            self.value
        )

    @property
    def resolved_label(self):
        return self.label or self.field.label

    def dump(self, owner=None, collection=None):
        print(("%s: %s" % (self.resolved_label, self.value)))

    BROWSE_VALUE_REGEX = re.compile(r"^((a|the|an) +|[^\w]+)+", re.I)

    @staticmethod
    def make_browse_value(value):
        # try to decompose unicode characters
        if isinstance(value, str):
            value = unicodedata.normalize('NFD', value)
            value = value.encode('ascii', 'ignore').decode()
        # remove other special characters
        return FieldValue.BROWSE_VALUE_REGEX.sub('', value or '')[:32]

    class Meta:
        app_label = 'data'
        ordering = ['order']
        index_together = [
            ['record', 'field'],
            ['field', 'record', 'index_value'],
            ['field', 'record', 'browse_value'],
        ]


@total_ordering
class DisplayFieldValue(FieldValue):
    """
    Represents a mapped field value for display.  Cannot be saved.
    """

    class Meta:
        app_label = 'data'

    def save(self, *args, **kwargs):
        raise NotImplementedError()

    def __cmp__(self, other):
        order_by = ('_original_field_name', 'group', 'order', 'refinement')
        for ob in order_by:
            s = getattr(self, ob)
            o = getattr(other, ob)
            if s != o:
                return (s > o) - (s < o)
        return 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    @staticmethod
    def from_value(value, field):
        dfv = DisplayFieldValue(
            record=value.record,
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
            context_id=value.context_id
        )
        dfv._original_field_name = value.field.name
        return dfv


def standardfield(field, standard='dc', equiv=False):
    f = Field.objects.get(standard__prefix=standard, name=field)
    if equiv:
        return Field.objects.filter(
            Q(id=f.id) | Q(id__in=f.get_equivalent_fields()))
    else:
        return f


def standardfield_ids(field, standard='dc', equiv=False):
    try:
        f = Field.objects.get(standard__prefix=standard, name=field)
    except Field.DoesNotExist:
        return []
    if equiv:
        ids = Field.objects.filter(
            Q(id=f.id) |
            Q(id__in=f.get_equivalent_fields())
        ).values_list('id', flat=True)
    else:
        ids = [f.id]
    return ids


class RemoteMetadata(models.Model):

    collection = models.ForeignKey('Collection')
    storage = models.ForeignKey('storage.Storage')
    url = models.CharField(max_length=255)
    mapping_url = models.CharField(max_length=255)
    last_modified = models.CharField(max_length=100, null=True, blank=True)


def create_data_fixtures(sender, *args, **kwargs):

    if sender.name != 'rooibos.data':
        return

    print("Creating data fixtures")

    # Metadata standars

    dc, created = MetadataStandard.objects.get_or_create(
        name='dublin-core',
        defaults=dict(
            prefix='dc',
            title='Dublin Core',
        )
    )

    tag, created = MetadataStandard.objects.get_or_create(
        name='tagging',
        defaults=dict(
            prefix='tag',
            title='Tagging',
        )
    )

    vra, created = MetadataStandard.objects.get_or_create(
        name='vra-core-4',
        defaults=dict(
            prefix='vra',
            title='VRA Core 4',
        )
    )

    # Fieldsets

    dcfs, created = FieldSet.objects.get_or_create(
        name='dc',
        defaults=dict(
            standard=1,
            title='Dublin Core',
        )
    )

    vrafs, created = FieldSet.objects.get_or_create(
        name='vra-core-4',
        defaults=dict(
            standard=1,
            title='VRA Core 4',
        )
    )

    # Fields

    fields = [
        (1, [17, 22], dc, "contributor", "Contributor"),
        (2, [18, 19, 22, 29], dc, "coverage", "Coverage"),
        (3, [17], dc, "creator", "Creator"),
        (4, [19], dc, "date", "Date"),
        (5, [20], dc, "description", "Description"),
        (6, [23, 24, 31], dc, "format", "Format"),
        (7, [32], dc, "identifier", "Identifier"),
        (8, [], dc, "language", "Language"),
        (9, [], dc, "publisher", "Publisher"),
        (10, [25], dc, "relation", "Relation"),
        (11, [26], dc, "rights", "Rights"),
        (12, [27], dc, "source", "Source"),
        (13, [16, 30], dc, "subject", "Subject"),
        (14, [], dc, "title", "Title"),
        (15, [34], dc, "type", "Type"),
        (16, [13], tag, "tags", "Tags"),
        (17, [1, 3], vra, "agent", "Agent"),
        (18, [2], vra, "culturalcontext", "Cultural Context"),
        (19, [2, 4], vra, "date", "Date"),
        (20, [5], vra, "description", "Description"),
        (21, [], vra, "inscription", "Inscription"),
        (22, [1, 2], vra, "location", "Location"),
        (23, [6], vra, "material", "Material"),
        (24, [6], vra, "measurements", "Measurements"),
        (25, [10], vra, "relation", "Relation"),
        (26, [11], vra, "rights", "Rights"),
        (27, [12], vra, "source", "Source"),
        (28, [], vra, "stateedition", "State/Edition"),
        (29, [2], vra, "styleperiod", "Style/Period"),
        (30, [13], vra, "subject", "Subject"),
        (31, [6], vra, "technique", "Technique"),
        (32, [7], vra, "textref", "Textual Reference"),
        (33, [], vra, "title", "Title"),
        (34, [15], vra, "worktype", "Work Type"),
    ]

    f = dict()
    for id, equiv, standard, name, label in fields:
        f[id], created = Field.objects.get_or_create(
            name=name,
            standard=standard,
            defaults=dict(
                label=label,
            )
        )
    for id, equiv, standard, name, label in fields:
        for e in equiv:
            f[id].equivalent.add(f[e])

    # Fieldset fields

    fieldsetfields = [
        (1, 34, vrafs, 0),
        (1, 20, vrafs, 0),
        (1, 21, vrafs, 0),
        (1, 22, vrafs, 0),
        (1, 23, vrafs, 0),
        (1, 24, vrafs, 0),
        (1, 25, vrafs, 0),
        (1, 26, vrafs, 0),
        (1, 27, vrafs, 0),
        (1, 28, vrafs, 0),
        (1, 29, vrafs, 0),
        (1, 30, vrafs, 0),
        (1, 31, vrafs, 0),
        (1, 32, vrafs, 0),
        (1, 33, vrafs, 0),
        (1, 19, vrafs, 0),
        (1, 18, vrafs, 0),
        (1, 17, vrafs, 0),
        (1, 7, dcfs, 1),
        (10, 14, dcfs, 2),
        (10, 5, dcfs, 3),
        (10, 3, dcfs, 4),
        (8, 2, dcfs, 5),
        (8, 4, dcfs, 6),
        (6, 15, dcfs, 7),
        (8, 13, dcfs, 8),
        (1, 1, dcfs, 9),
        (6, 6, dcfs, 10),
        (1, 8, dcfs, 11),
        (1, 9, dcfs, 12),
        (1, 11, dcfs, 13),
        (1, 10, dcfs, 14),
        (1, 12, dcfs, 15),
    ]

    for importance, field, fieldset, order in fieldsetfields:
        FieldSetField.objects.get_or_create(
            fieldset=fieldset,
            field=f[field],
            defaults=dict(
                importance=importance,
                order=order,
                label=f[field].label,
            )
        )


signals.post_migrate.connect(create_data_fixtures)
