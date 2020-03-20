from rooibos.access.functions import filter_by_access
from rooibos.data.models import FieldSet
from rooibos.userprofile.views import load_settings, store_settings
from .models import Collection, Field, MetadataStandard, FieldValue, Record, \
    CollectionItem
from django.core import serializers
from django.core.serializers.json import Serializer as JsonSerializer
from django.core.exceptions import ObjectDoesNotExist
from django.db import DEFAULT_DB_ALIAS, reset_queries

import logging


COLLECTION_VISIBILITY_PREFERENCES = 'data_collection_visibility_prefs'


def get_collection_visibility_preferences(user):
    setting = load_settings(user, COLLECTION_VISIBILITY_PREFERENCES).get(
        COLLECTION_VISIBILITY_PREFERENCES, ['show:']
    )
    try:
        mode, ids = setting[0].split(':')
        ids = list(map(int, ids.split(','))) if ids else []
    except ValueError:
        mode = 'show'
        ids = []
    return mode, ids


def set_collection_visibility_preferences(user, mode, ids):
    value = '%s:%s' % (mode, ','.join(ids))
    return store_settings(user,
                          COLLECTION_VISIBILITY_PREFERENCES,
                          value)


def apply_collection_visibility_preferences(user, queryset):
    mode, ids = get_collection_visibility_preferences(user)
    if mode == 'show':
        return queryset.exclude(id__in=ids)
    else:
        return queryset.filter(id__in=ids)


class RenamingSerializer(JsonSerializer):

    def __init__(self, prefix=None):
        super(RenamingSerializer, self).__init__()
        self.prefix = prefix

    def end_object(self, obj):
        if self.prefix:
            if 'record' in self._current:
                self._current['record'] = (
                    self.prefix + self._current['record'][0],
                )
            if 'collection' in self._current:
                self._current['collection'] = (
                    self.prefix + self._current['collection'][0],
                )
            if str(obj._meta) in ('data.collection', 'data.record'):
                self._current['name'] = self.prefix + self._current['name']
        return super(RenamingSerializer, self).end_object(obj)


def collection_dump(user, identifier, stream=None, prefix=None):

    # export collection
    collection = filter_by_access(user, Collection).get(id=identifier)

    # export collection items and records
    collectionitems = list(
        CollectionItem.objects
        .select_related('record', 'collection')
        .filter(collection__id=identifier)
    )
    ids = [collectionitem.record_id for collectionitem in collectionitems]
    records = list(Record.filter_by_access(user, *ids).filter(owner=None))
    ids = [record.id for record in records]
    collectionitems = [collectionitem for collectionitem in collectionitems
                       if collectionitem.record_id in ids]

    # export all fieldvalues
    fieldvalues = FieldValue.objects.select_related('record', 'field').filter(
        record__id__in=ids)

    used_fields = set(fieldvalue.field_id for fieldvalue in fieldvalues)

    # export all used fields
    fields = list(Field.objects.filter(id__in=used_fields).distinct())

    # export equivalent fields
    more = True
    while more:
        eq_ids = set(
            id
            for field in fields
            for id in field.equivalent.values_list('id', flat=True)
            if id not in used_fields
        )
        more = len(eq_ids) > 0
        if more:
            eq_fields = Field.objects.filter(id__in=eq_ids)
            fields.extend(eq_fields)
            used_fields = used_fields.union(eq_ids)

    # export all used standards
    standards = MetadataStandard.objects.filter(id__in=set(
        field.standard_id for field in fields if field.standard_id
    ))

    objects = [collection]
    objects.extend(standards)
    objects.extend(fields)
    objects.extend(collectionitem.record for collectionitem in collectionitems)
    objects.extend(collectionitems)
    objects.extend(fieldvalues)

    serializer = RenamingSerializer(prefix)
    kwargs = dict()
    if stream:
        kwargs['stream'] = stream
    return serializer.serialize(objects, use_natural_keys=True, **kwargs)


def collection_load(user, json, **options):

    db = options.pop('using', DEFAULT_DB_ALIAS)

    logging.debug("Starting collection load")

    for obj in serializers.deserialize('json', json):

        pk = None

        manager = obj.object._default_manager.db_manager(db)
        if hasattr(manager, 'get_by_natural_key'):
            try:
                pk = manager.get_by_natural_key(*obj.object.natural_key()).pk
            except ObjectDoesNotExist:
                pass

            logging.debug("%s with natural key %s %sfound" % (
                obj.object._meta.object_name,
                obj.object.natural_key(),
                '' if pk else 'not ',
            ))
        else:
            logging.debug(
                "%s without natural key" % obj.object._meta.object_name)

        obj.object.pk = pk

        logging.debug("%s %s" % (obj, obj.object))
        obj.save()

        if pk and obj.object._meta.object_name == 'Record':
            # found existing record, remove fieldvalues
            fieldvalues = obj.object.fieldvalue_set.filter(
                owner=None, context_type=None, context_id=None)
            if fieldvalues:
                logging.debug("Deleting %d fieldvalues" % len(fieldvalues))
                fieldvalues.delete()

        if obj.object._meta.object_name == 'FieldValue':
            # need to call custom save method on FieldValue objects
            obj.object.save()

        reset_queries()

    logging.debug("Collection load complete")


def get_fields_for_set(set_name):
    fields = dict()
    try:
        fields.update(
            (field.id, None)
            for field in
            FieldSet.objects.get(
                name='metadata-%s' % set_name
            ).fields.all()
        )
    except FieldSet.DoesNotExist:
        pass
    return fields
