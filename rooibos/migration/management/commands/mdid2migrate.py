from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db import reset_queries, IntegrityError
from rooibos.access.models import AccessControl, ExtendedGroup, Subnet, \
    AttributeValue, ATTRIBUTE_BASED_GROUP, IP_BASED_GROUP
from ipaddr import IPNetwork
from tagging.models import Tag, TaggedItem
from rooibos.data.models import Collection, CollectionItem, Field, \
    FieldValue, Record, FieldSet, FieldSetField, Vocabulary, VocabularyTerm, \
    MetadataStandard
from rooibos.migration.models import ObjectHistory, content_hash
from rooibos.presentation.models import Presentation, PresentationItem
from rooibos.storage.models import Storage, Media
from rooibos.util.models import OwnedWrapper
from rooibos.util.progressbar import ProgressBar
from xml.dom import minidom
import logging
import os
import pyodbc
import re


# MDID2 permissions
P = dict(
    _None=0,
    ModifyACL=1 << 0,
    CreateCollection=1 << 1,
    ManageCollection=1 << 2,
    DeleteCollection=1 << 3,
    ModifyImages=1 << 5,
    ReadCollection=1 << 7,
    CreateSlideshow=1 << 8,
    ModifySlideshow=1 << 9,
    DeleteSlideshow=1 << 10,
    ViewSlideshow=1 << 11,
    CopySlideshow=1 << 12,
    FullSizedImages=1 << 13,
    AnnotateImages=1 << 14,
    ManageUsers=1 << 15,
    ImageViewerAccess=1 << 16,
    PublishSlideshow=1 << 17,
    ResetPassword=1 << 18,
    ManageAnnouncements=1 << 21,
    ManageControlledLists=1 << 23,
    ManageCollectionGroups=1 << 25,
    UserOptions=1 << 26,
    PersonalImages=1 << 27,
    ShareImages=1 << 28,
    SuggestImages=1 << 29,
    Unknown=1 << 31,
)

IMAGE_SHARED = 1
IMAGE_SUGGESTED = 2
IMAGE_REJECTED = 4


STATIC_CONTENT_HASH = content_hash('static')


class MergeObjectsException(Exception):

    def __init__(self, instance):
        super(MergeObjectsException, self).__init__()
        self.instance = instance


class MigrateModel(object):

    instance_maps = dict()

    def __init__(self, cursor, model, query, label=None, m2m_model=None,
                 type=None):
        self.model = model
        self.cursor = cursor
        self.type = type
        self.m2m_model = m2m_model
        self.model_name = label or (
            model._meta.verbose_name_plural.title() + (
                '' if not m2m_model
                else '->' + m2m_model._meta.verbose_name_plural.title()
            )
        )
        self.instance_map = MigrateModel.instance_maps.setdefault(
            model._meta.verbose_name_raw.replace(' ', '') +
            ('' if not m2m_model else '_' + m2m_model._meta.verbose_name_raw),
            dict()
        )
        self.content_type = ContentType.objects.get_for_model(model)
        if not m2m_model:
            self.m2m_content_type = None
        else:
            self.m2m_content_type = ContentType.objects.get_for_model(
                m2m_model)
        q = ObjectHistory.objects.filter(
            content_type=self.content_type,
            m2m_content_type=self.m2m_content_type,
            type=self.type
        )
        self.preserve_memory = q.count() > 100000
        if self.preserve_memory:
            self.object_history = dict(
                (original_id, int(hash, 16))
                for original_id, hash
                in q.values_list('original_id', 'content_hash')
            )
        else:
            self.object_history = dict((o.original_id, o) for o in q)
        self.added = self.updated = self.deleted = self.unchanged = \
            self.recreated = self.errors = self.nohistory = 0
        self.need_instance_map = False
        self.supports_deletion = True
        self.query = query
        self.force_migration = False

    def hash(self, row):
        return STATIC_CONTENT_HASH

    def update(self, instance, row):
        pass

    def create(self, row):
        instance = self.create_instance(row)
        if instance:
            self.update(instance, row)
        return instance

    def create_instance(self, row):
        return self.model()

    def post_save(self, instance, row):
        pass

    def m2m_create(self, row):
        # needs to return (object_id, m2m_object_id) tuple
        raise NotImplemented

    def m2m_delete(self, object_id, m2m_object_id):
        raise NotImplemented

    def key(self, row):
        return str(row.ID)

    def run(self, step=None, steps=None):

        def compare_hash(historic, current):
            if self.preserve_memory:
                return historic == int(current, 16)
            else:
                return historic.content_hash == current

        print("\n%sMigrating %s" % (
            'Step %s of %s: ' % (step, steps) if step and steps else '',
            self.model_name
        ))
        r = re.match('^SELECT (.+) FROM (.+)$', self.query)
        pb = ProgressBar(
            list(
                self.cursor.execute("SELECT COUNT(*) FROM %s" % r.groups()[1])
            )[0][0]
        ) if r else None
        count = 0
        merged_ids = dict()
        logging.debug('Running query against MDID2 database: %s' % self.query)
        for row in self.cursor.execute(self.query):
            hash = self.hash(row)
            h = self.object_history.pop(self.key(row), None)
            create = True
            if h:
                if not self.force_migration and (
                        compare_hash(h, hash) or self.m2m_model):
                    # object unchanged, don't need to do anything
                    # or, we're working on a many-to-many relation,
                    # don't need to do anything on the instance
                    logging.debug('%s %s unchanged in source, skipping' % (
                        self.model_name, self.key(row)))
                    create = False
                    self.unchanged += 1
                elif not self.force_migration and \
                        compare_hash(h, STATIC_CONTENT_HASH):
                    # object may have changed, but we don't have the hash
                    # of the previous version
                    # so we can't know.  Just store the new hash in the
                    # history to be able
                    # to track future changes
                    if self.preserve_memory:
                        h = ObjectHistory.objects.get(
                            content_type=self.content_type,
                            m2m_content_type=self.m2m_content_type,
                            type=self.type,
                            original_id=self.key(row)
                        )
                    h.content_hash = hash
                    h.save()
                    create = False
                    self.nohistory += 1
                else:
                    if self.preserve_memory:
                        h = ObjectHistory.objects.get(
                            content_type=self.content_type,
                            m2m_content_type=self.m2m_content_type,
                            type=self.type,
                            original_id=self.key(row)
                        )
                    # object changed, need to update
                    try:
                        instance = self.model.objects.get(id=h.object_id)
                        create = False
                    except ObjectDoesNotExist:
                        instance = None
                    if not instance:
                        # object has been deleted, need to recreate
                        logging.debug(
                            '%s %s changed and not in destination, '
                            'recreating' % (self.model_name, row.ID))
                        h.delete()
                        self.recreated += 1
                    else:
                        # update existing object
                        logging.debug('%s %s changed, updating' % (
                            self.model_name, self.key(row)))
                        self.update(instance, row)
                        try:
                            instance.save()
                            self.post_save(instance, row)
                            h.content_hash = hash
                            h.save()
                            self.updated += 1
                        except (IntegrityError, pyodbc.IntegrityError) as ex:
                            logging.error(
                                "Integrity error: %s %s" % (
                                    self.model_name, self.key(row)))
                            logging.error(ex)
                            self.errors += 1
            if create:
                # object does not exist, need to create
                logging.debug('%s %s not in destination, creating' % (
                    self.model_name, self.key(row)))
                if not self.m2m_model:
                    try:
                        instance = self.create(row)
                        if instance:
                                instance.save()
                                self.post_save(instance, row)
                                ObjectHistory.objects.create(
                                    content_type=self.content_type,
                                    object_id=instance.id,
                                    type=self.type,
                                    original_id=self.key(row),
                                    content_hash=hash,
                                )
                                self.added += 1
                        else:
                            logging.error("No instance created: %s %s" % (
                                self.model_name, self.key(row)))
                            self.errors += 1
                    except (IntegrityError, pyodbc.IntegrityError,
                            ValueError) as ex:
                        logging.error("%s: %s %s" % (
                            type(ex).__name__, self.model_name, self.key(row)))
                        logging.error(ex)
                        self.errors += 1
                    except MergeObjectsException as ex:
                        merged_ids[self.key(row)] = ex.instance
                else:
                    # need to create many-to-many relation
                    object_id, m2m_object_id = self.m2m_create(row)
                    if object_id and m2m_object_id:
                        ObjectHistory.objects.create(
                            content_type=self.content_type,
                            object_id=object_id,
                            m2m_content_type=self.m2m_content_type,
                            m2m_object_id=m2m_object_id,
                            type=self.type,
                            original_id=self.key(row),
                            content_hash=hash,
                        )
                        self.added += 1
                    else:
                        logging.error("No instance created: %s %s" % (
                            self.model_name, self.key(row)))
                        self.errors += 1
            count += 1
            if not (count % 1000):
                reset_queries()
            if pb:
                pb.update(count)
        if pb:
            pb.done()
        reset_queries()
        if self.object_history and self.supports_deletion:
            print("Removing unused objects")
            pb = ProgressBar(len(self.object_history))
            count = 0
            # Delete many objects at once for better performance
            to_delete = []
            for oid, o in self.object_history.items():
                if self.preserve_memory:
                    o = ObjectHistory.objects.get(
                        content_type=self.content_type,
                        m2m_content_type=self.m2m_content_type,
                        type=self.type,
                        original_id=oid
                    )
                # these objects have been deleted since the last migration
                logging.debug('%s %s not in source, deleting' % (
                    self.model_name, o.original_id))
                if not self.m2m_model:
                    to_delete.append(o)
                    if len(to_delete) >= 1000:
                        self.model.objects.filter(
                            id__in=[d.object_id for d in to_delete]).delete()
                        ObjectHistory.objects.filter(
                            id__in=[d.id for d in to_delete]).delete()
                        to_delete = []
                else:
                    self.m2m_delete(
                        object_id=o.object_id, m2m_object_id=o.m2m_object_id)
                    o.delete()
                self.deleted += 1
                count += 1
                if count % 1000 == 0:
                    reset_queries()
                pb.update(count)
            if to_delete:
                self.model.objects.filter(
                    id__in=[d.object_id for d in to_delete]).delete()
                ObjectHistory.objects.filter(
                    id__in=[d.id for d in to_delete]).delete()
            pb.done()
            reset_queries()
        if self.need_instance_map and not self.m2m_model:
            print("Retrieving instances")
            ids = dict(ObjectHistory.objects.filter(
                content_type=self.content_type,
                m2m_content_type=None,
                type=self.type
            ).values_list('object_id', 'original_id'))
            self.instance_map.update(
                (ids.get(o.id, None), o) for o in self.model.objects.all())
            self.instance_map.update(merged_ids)

        print("  Added\tReadded\tDeleted\tUpdated\t  Unch.\t Merged\t" \
              " Errors\tNo hist")
        print("%7d\t%7d\t%7d\t%7d\t%7d\t%7d\t%7d\t%7d" % (
            self.added, self.recreated, self.deleted, self.updated,
            self.unchanged, len(merged_ids), self.errors, self.nohistory
        ))


class MigrateUsers(MigrateModel):

    def __init__(self, cursor):
        super(MigrateUsers, self).__init__(
            cursor=cursor,
            model=User,
            query="SELECT ID,Login,Password,Name,FirstName,Email,"
            "Administrator,LastAuthenticated FROM users"
        )
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(
            row.Login, row.Password, row.Name, row.FirstName, row.Email,
            row.Administrator
        )

    def update(self, instance, row):
        instance.username = row.Login[:30]
        if row.Password:
            instance.password = row.Password.lower()
        else:
            instance.set_unusable_password()
        instance.last_name = row.Name[:30] if row.Name else ''
        instance.first_name = row.FirstName[:30] if row.FirstName else ''
        instance.email = row.Email[:75] if row.Email else ''
        instance.is_superuser = instance.is_staff = row.Administrator

    def create_instance(self, row):
        try:
            instance = User.objects.get(username=row.Login[:30])
            raise MergeObjectsException(instance)
        except User.DoesNotExist:
            pass
        return User(last_login=row.LastAuthenticated or datetime(1980, 1, 1))


class MigrateGroups(MigrateModel):

    def __init__(self, cursor):
        super(MigrateGroups, self).__init__(
            cursor=cursor,
            model=Group,
            query="SELECT ID,Title,Type FROM usergroups"
        )
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(row.Title, row.Type)

    def update(self, instance, row):
        instance.name = row.Title

    def create_instance(self, row):
        return Group() if row.Type == 'M' else ExtendedGroup(type=row.Type)


class MigrateSubnet(MigrateModel):

    def __init__(self, cursor):
        self.usergroups = MigrateModel.instance_maps['group']
        super(MigrateSubnet, self).__init__(
            cursor=cursor,
            model=Subnet,
            query="SELECT GroupID,Subnet,Mask FROM usergroupipranges"
        )

    def key(self, row):
        return '%s %s %s' % (row.GroupID, row.Subnet, row.Mask)

    def create_instance(self, row):
        try:
            group = ExtendedGroup.objects.get(
                id=self.usergroups[str(row.GroupID)].id, type=IP_BASED_GROUP)
            return Subnet(
                group=group,
                subnet=str(IPNetwork('%s/%s' % (row.Subnet, row.Mask)))
            )
        except ExtendedGroup.DoesNotExist:
            return None
        except KeyError:
            return None


class MigrateAttribute(MigrateModel):

    def __init__(self, cursor):
        self.usergroups = MigrateModel.instance_maps['group']
        super(MigrateAttribute, self).__init__(
            cursor=cursor,
            model=AttributeValue,
            query="SELECT GroupID,Attribute,AttributeValueInstance,"
            "AttributeValue FROM usergroupattributes"
        )

    def key(self, row):
        return '%s %s %s' % (
            row.GroupID, row.Attribute, row.AttributeValueInstance)

    def hash(self, row):
        return content_hash(row.AttributeValue)

    def update(self, instance, row):
        instance.value = row.AttributeValue

    def create_instance(self, row):
        try:
            group = ExtendedGroup.objects.get(
                id=self.usergroups[str(row.GroupID)].id,
                type=ATTRIBUTE_BASED_GROUP
            )
            attr, created = group.attribute_set.get_or_create(
                attribute=row.Attribute)
            return attr.attributevalue_set.create(value=row.AttributeValue)
        except ExtendedGroup.DoesNotExist:
            return None
        except KeyError:
            return None


class MigrateMembers(MigrateModel):

    def __init__(self, cursor):
        self.usergroups = MigrateModel.instance_maps['group']
        self.users = MigrateModel.instance_maps['user']
        super(MigrateMembers, self).__init__(
            cursor=cursor,
            model=Group,
            m2m_model=User,
            label='Group Members',
            query="SELECT UserID,GroupID FROM usergroupmembers"
        )

    def key(self, row):
        return '%s %s' % (row.UserID, row.GroupID)

    def m2m_create(self, row):
        group = self.usergroups.get(str(row.GroupID))
        user = self.users.get(str(row.UserID))
        if group and user:
            group.user_set.add(user)
            return group.id, user.id
        else:
            return None, None

    def m2m_delete(self, object_id, m2m_object_id):
        try:
            Group.objects.get(id=object_id).user_set.remove(
                User.objects.get(id=m2m_object_id))
        except Group.DoesNotExist:
            pass
        except User.DoesNotExist:
            pass


class MigrateCollectionGroups(MigrateModel):

    def __init__(self, cursor):
        super(MigrateCollectionGroups, self).__init__(
            cursor=cursor,
            model=Collection,
            label='Collection Groups',
            type='group',
            query="SELECT ID,Title FROM collectiongroups"
        )
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(row.Title)

    def update(self, instance, row):
        instance.title = row.Title


class MigrateCollections(MigrateModel):

    def __init__(self, cursor):
        super(MigrateCollections, self).__init__(
            cursor=cursor,
            model=Collection,
            query="SELECT ID,Title,Type,Description,UsageAgreement "
            "FROM collections"
        )
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(row.Title, row.Description, row.UsageAgreement)

    def update(self, instance, row):
        instance.title = row.Title
        instance.description = row.Description
        instance.agreement = row.UsageAgreement


class MigrateStorages(MigrateModel):

    def __init__(self, cursor):
        super(MigrateStorages, self).__init__(
            cursor=cursor,
            model=Storage,
            query="SELECT ID,Title,ResourcePath FROM collections "
            "WHERE Type IN ('I', 'N', 'R')"
        )
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(row.Title, row.ResourcePath)

    def update(self, instance, row):
        instance.title = row.Title
        instance.base = row.ResourcePath.replace('\\', '/')

    def create_instance(self, row):
        return Storage(system='local')


class MigrateFieldSets(MigrateModel):

    def __init__(self, cursor):
        super(MigrateFieldSets, self).__init__(
            cursor=cursor,
            model=FieldSet,
            query="SELECT ID,Title FROM collections"
        )
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(row.Title)

    def update(self, instance, row):
        instance.title = row.Title


class MigrateCollectionParents(MigrateModel):

    def __init__(self, cursor):
        self.collections = MigrateModel.instance_maps['collection']
        super(MigrateCollectionParents, self).__init__(
            cursor=cursor,
            model=Collection,
            m2m_model=Collection,
            label='Collection Hierarchy',
            query="SELECT ID,GroupID FROM collections WHERE GroupID>0"
        )

    def key(self, row):
        return '%s %s' % (row.ID, row.GroupID)

    def m2m_create(self, row):
        collection = self.collections.get(str(row.ID))
        parent = self.collections.get(str(row.GroupID))
        if collection and parent:
            parent.children.add(collection)
            return collection.id, parent.id
        else:
            return None, None

    def m2m_delete(self, object_id, m2m_object_id):
        try:
            Collection.objects.get(id=m2m_object_id).children.remove(
                Collection.objects.get(id=object_id))
        except Collection.DoesNotExist:
            pass


class MigrateControlledLists(MigrateModel):

    def __init__(self, cursor):
        super(MigrateControlledLists, self).__init__(
            cursor=cursor,
            model=Vocabulary,
            query="SELECT ID,Title,Description,Standard,Origin "
            "FROM controlledlists"
        )
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(
            row.Title, row.Description, row.Standard, row.Origin)

    def update(self, instance, row):
        instance.title = row.Title
        instance.description = row.Description
        instance.standard = row.Standard
        instance.origin = row.Origin


class MigrateControlledListItems(MigrateModel):

    def __init__(self, cursor):
        super(MigrateControlledListItems, self).__init__(
            cursor=cursor,
            model=VocabularyTerm,
            query="SELECT ID,ControlledListID,ItemValue "
            "FROM controlledlistvalues"
        )
        self.vocabularies = MigrateModel.instance_maps['vocabulary']

    def hash(self, row):
        return content_hash(row.ItemValue)

    def update(self, instance, row):
        instance.term = row.ItemValue

    def create_instance(self, row):
        if str(row.ControlledListID) not in self.vocabularies:
            return None
        return VocabularyTerm(
            vocabulary=self.vocabularies[str(row.ControlledListID)])


class MigrateRecords(MigrateModel):

    def __init__(self, cursor):
        super(MigrateRecords, self).__init__(
            cursor=cursor,
            model=Record,
            query="SELECT ID,Resource,Created,Modified,RemoteID,CachedUntil,"
            "Expires,UserID,Flags FROM images"
        )
        self.need_instance_map = True
        self.collections = MigrateModel.instance_maps['collection']
        self.users = MigrateModel.instance_maps['user']

    def hash(self, row):
        return content_hash(
            row.Modified, row.RemoteID, row.CachedUntil, row.Expires,
            row.UserID
        )

    def update(self, instance, row):
        if row.UserID > 0 and str(row.UserID) not in self.users:
            raise IntegrityError()
        instance.modified = row.Modified
        instance.source = row.RemoteID
        instance.next_update = row.CachedUntil or row.Expires
        if row.UserID > 0:
            instance.owner = self.users[str(row.UserID)]
        else:
            instance.owner = None

    def create_instance(self, row):
        return Record(created=row.Created or row.Modified or datetime.now(),
                      name=row.Resource.rsplit('.', 1)[0])


class MigrateCollectionItems(MigrateModel):

    def __init__(self, cursor):
        self.collections = MigrateModel.instance_maps['collection']
        self.records = MigrateModel.instance_maps['record']
        super(MigrateCollectionItems, self).__init__(
            cursor=cursor,
            model=CollectionItem,
            query="SELECT ID,CollectionID,Flags FROM images"
        )

    def hash(self, row):
        return content_hash(row.CollectionID, (row.Flags or 0) & IMAGE_SHARED)

    def update(self, instance, row):
        if str(row.CollectionID) not in self.collections or \
                str(row.ID) not in self.records:
            raise IntegrityError()
        instance.collection = self.collections[str(row.CollectionID)]
        instance.hidden = bool(
            self.records[str(row.ID)].owner and
            not ((row.Flags or 0) & IMAGE_SHARED)
        )

    def create_instance(self, row):
        if str(row.ID) not in self.records:
            return None
        return CollectionItem(record=self.records[str(row.ID)])


class MigrateMedia(MigrateModel):

    remove_full_prefix = False

    def __init__(self, cursor):
        super(MigrateMedia, self).__init__(
            cursor=cursor,
            model=Media,
            query="SELECT ID,Resource,CollectionID FROM images"
        )
        self.storages = MigrateModel.instance_maps['storage']
        self.records = MigrateModel.instance_maps['record']

    def hash(self, row):
        return content_hash(row.Resource)

    def update(self, instance, row):
        if self.remove_full_prefix:
            instance.url = row.Resource.strip()
        else:
            instance.url = os.path.join('full', row.Resource.strip())

    def create_instance(self, row):
        if str(row.ID) not in self.records or \
                str(row.CollectionID) not in self.storages:
            return None
        return Media(record=self.records[str(row.ID)],
                     name=row.Resource.rsplit('.', 1)[0],
                     storage=self.storages[str(row.CollectionID)],
                     mimetype='image/jpeg')


class MigrateRecordSuggestions(MigrateModel):

    def __init__(self, cursor):
        super(MigrateRecordSuggestions, self).__init__(
            cursor=cursor,
            model=TaggedItem,
            type='suggest',
            label='Suggested Records',
            query="SELECT ID,UserID,Flags FROM images "
            "WHERE UserID>0 AND Flags&2=2 AND Flags&4=0"
        )
        self.users = MigrateModel.instance_maps['user']
        self.records = MigrateModel.instance_maps['record']
        self.suggested_tag, created = Tag.objects.get_or_create(
            name='suggested')
        self.record_content_type = ContentType.objects.get_for_model(Record)

    def create_instance(self, row):
        if str(row.UserID) not in self.users or \
                str(row.ID) not in self.records:
            return None
        wrapper = OwnedWrapper.objects.get_for_object(
            user=self.users[str(row.UserID)],
            object_id=self.records[str(row.ID)].id,
            type=self.record_content_type)
        return TaggedItem(tag=self.suggested_tag, object=wrapper)


class MigrateFavoriteImages(MigrateModel):

    def __init__(self, cursor):
        super(MigrateFavoriteImages, self).__init__(
            cursor=cursor,
            model=TaggedItem,
            type='favorite',
            label='Favorite Records',
            query="SELECT UserID,ImageID FROM favoriteimages"
        )
        self.users = MigrateModel.instance_maps['user']
        self.records = MigrateModel.instance_maps['record']
        self.favorite_tag, created = Tag.objects.get_or_create(name='favorite')
        self.record_content_type = ContentType.objects.get_for_model(Record)

    def key(self, row):
        return '%s %s' % (row.UserID, row.ImageID)

    def create_instance(self, row):
        if str(row.UserID) not in self.users or \
                str(row.ImageID) not in self.records:
            return None
        wrapper = OwnedWrapper.objects.get_for_object(
            user=self.users[str(row.UserID)],
            object_id=self.records[str(row.ImageID)].id,
            type=self.record_content_type)
        return TaggedItem(tag=self.favorite_tag, object=wrapper)


class MigrateImageNotes(MigrateModel):

    def __init__(self, cursor):
        super(MigrateImageNotes, self).__init__(
            cursor=cursor,
            model=FieldValue,
            type='annotate',
            label='Annotations',
            query="SELECT ImageID,UserID,Annotation FROM imageannotations"
        )
        self.users = MigrateModel.instance_maps['user']
        self.records = MigrateModel.instance_maps['record']
        self.description_field = Field.objects.get(
            standard__prefix='dc', name='description')

    def key(self, row):
        return '%s %s' % (row.UserID, row.ImageID)

    def update(self, instance, row):
        instance.value = row.Annotation

    def create_instance(self, row):
        if str(row.UserID) not in self.users \
                or str(row.ImageID) not in self.records:
            return None
        return FieldValue(record=self.records[str(row.ImageID)],
                          field=self.description_field,
                          owner=self.users[str(row.UserID)],
                          label='Note',
                          order=1000)


class MigratePresentations(MigrateModel):

    def __init__(self, cursor):
        super(MigratePresentations, self).__init__(
            cursor=cursor,
            model=Presentation,
            query="SELECT ID,UserID,Title,Description,AccessPassword,"
            "CreationDate,ModificationDate,ArchiveFlag FROM slideshows"
        )
        self.users = MigrateModel.instance_maps['user']
        self.need_instance_map = True

    def hash(self, row):
        return content_hash(
            row.Title, row.UserID, row.Description, row.ArchiveFlag,
            row.AccessPassword
        )

    def update(self, instance, row):
        instance.title = row.Title
        instance.owner = self.users[str(row.UserID)]
        instance.description = row.Description
        instance.hidden = row.ArchiveFlag
        instance.password = row.AccessPassword[:32] \
            if row.AccessPassword else None

    def post_save(self, instance, row):
        instance.override_dates(
            created=row.CreationDate, modified=row.ModificationDate)

    def create_instance(self, row):
        if str(row.UserID) not in self.users:
            return None
        return Presentation()


class MigratePresentationFolders(MigrateModel):

    def __init__(self, cursor):
        super(MigratePresentationFolders, self).__init__(
            cursor=cursor,
            model=TaggedItem,
            type='folders',
            label='Presentation Folders',
            query="SELECT slideshows.ID,slideshows.UserID,folders.Title "
            "AS Title FROM slideshows INNER JOIN folders "
            "ON FolderID=folders.ID"
        )
        self.users = MigrateModel.instance_maps['user']
        self.presentations = MigrateModel.instance_maps['presentation']
        self.presentation_content_type = ContentType.objects.get_for_model(
            Presentation)

    def hash(self, row):
        return content_hash(row.Title)

    def update(self, instance, row):
        tag, created = Tag.objects.get_or_create(name=row.Title.strip())
        instance.tag = tag

    def create_instance(self, row):
        if str(row.UserID) not in self.users or \
                str(row.ID) not in self.presentations:
            return None
        wrapper = OwnedWrapper.objects.get_for_object(
            user=self.users[str(row.UserID)],
            object_id=self.presentations[str(row.ID)].id,
            type=self.presentation_content_type)
        return TaggedItem(object=wrapper)


class MigratePresentationItems(MigrateModel):

    def __init__(self, cursor):
        super(MigratePresentationItems, self).__init__(
            cursor=cursor,
            model=PresentationItem,
            query="SELECT ID,SlideshowID,ImageID,DisplayOrder,Scratch,"
            "Annotation FROM slides"
        )
        self.presentations = MigrateModel.instance_maps['presentation']
        self.records = MigrateModel.instance_maps['record']

    def hash(self, row):
        return content_hash(row.DisplayOrder, row.Annotation, row.Scratch)

    def update(self, instance, row):
        instance.order = row.DisplayOrder
        instance.hidden = row.Scratch
        instance.annotation = row.Annotation

    def create_instance(self, row):
        if str(row.ImageID) not in self.records or \
                str(row.SlideshowID) not in self.presentations:
            return None
        return PresentationItem(
            record=self.records[str(row.ImageID)],
            presentation=self.presentations[str(row.SlideshowID)]
        )


class MigrateFields(MigrateModel):

    def __init__(self, cursor):
        super(MigrateFields, self).__init__(
            cursor=cursor,
            model=Field,
            query="SELECT ID,Label,Name,ControlledListID FROM fielddefinitions"
        )
        self.vocabularies = MigrateModel.instance_maps['vocabulary']
        self.need_instance_map = True
        self.force_migration = True

    def hash(self, row):
        return content_hash(row.Label, row.Name, row.ControlledListID)

    def update(self, instance, row):
        instance.label = row.Label
        instance.old_name = row.Name
        instance.vocabulary = self.vocabularies.get(str(row.ControlledListID))

    def create_instance(self, row):
        return Field()


class MigrateEquivalentFields(MigrateModel):

    # TODO: handle change in hash in m2m migrations

    def __init__(self, cursor):
        super(MigrateEquivalentFields, self).__init__(
            cursor=cursor,
            model=Field,
            m2m_model=Field,
            type='equiv',
            label='Equivalent Fields',
            query="SELECT ID,DCElement,DCRefinement FROM fielddefinitions "
            "WHERE DCElement IS NOT NULL"
        )
        self.fields = MigrateModel.instance_maps['field']
        self.dc_fields = dict(
            (f.name, f) for f in Field.objects.filter(standard__prefix='dc')
        )
        self.qualified_dc_standard, created = \
            MetadataStandard.objects.get_or_create(
                prefix='dcqualified',
                defaults=dict(
                    title='Qualified Dublin Core',
                    name='qualified_dublin_core'
                )
            )

    def hash(self, row):
        return content_hash(row.DCElement, row.DCRefinement)

    def m2m_create(self, row):
        field = self.fields.get(str(row.ID))
        dc_field = self.dc_fields.get(row.DCElement.lower())
        if dc_field and row.DCRefinement:
            qdc_field, created = Field.objects.get_or_create(
                standard=self.qualified_dc_standard,
                name=('%s.%s' % (row.DCElement, row.DCRefinement)).lower(),
                defaults=dict(
                    label='%s %s' % (row.DCElement, row.DCRefinement)
                )
            )
            qdc_field.equivalent.add(dc_field)
            dc_field = qdc_field
        if dc_field:
            field.equivalent.add(dc_field)
            return field.id, dc_field.id
        else:
            return None, None

    def m2m_delete(self, object_id, m2m_object_id):
        try:
            Field.objects.get(id=object_id).equivalent.remove(
                Field.objects.get(id=m2m_object_id))
        except Field.DoesNotExist:
            pass


class MigrateFieldSetFields(MigrateModel):

    def __init__(self, cursor):
        super(MigrateFieldSetFields, self).__init__(
            cursor=cursor,
            model=FieldSetField,
            query="SELECT ID,CollectionID,Label,ShortView,MediumView,LongView,"
            "DisplayOrder FROM fielddefinitions"
        )
        self.fieldsets = MigrateModel.instance_maps['fieldset']
        self.fields = MigrateModel.instance_maps['field']

    def hash(self, row):
        return content_hash(
            row.Label, row.ShortView, row.MediumView, row.LongView)

    def update(self, instance, row):
        instance.fieldset = self.fieldsets.get(str(row.CollectionID))
        instance.field = self.fields.get(str(row.ID)) or instance.field
        instance.label = row.Label
        instance.order = row.DisplayOrder
        instance.importance = (row.ShortView and 4) + \
            (row.MediumView and 2) + (row.LongView and 1)

    def create_instance(self, row):
        return FieldSetField()


class MigrateFieldValues(MigrateModel):

    def __init__(self, cursor):
        super(MigrateFieldValues, self).__init__(
            cursor=cursor,
            model=FieldValue,
            query="SELECT fielddata.ID,ImageID,FieldID,FieldInstance,"
            "FieldValue,OriginalValue,Type,Label,DisplayOrder "
            "FROM fielddata INNER JOIN fielddefinitions "
            "ON FieldID=fielddefinitions.ID"
        )
        self.fields = MigrateModel.instance_maps['field']
        self.records = MigrateModel.instance_maps['record']

    def hash(self, row):
        return content_hash(row.Label, row.FieldValue, row.DisplayOrder)

    def update(self, instance, row):
        instance.label = row.Label
        instance.value = row.FieldValue
        instance.order = int(row.DisplayOrder) * 100 + int(row.FieldInstance)

    def create_instance(self, row):
        if str(row.ImageID) not in self.records or \
                str(row.FieldID) not in self.fields:
            return None
        return FieldValue(record=self.records[str(row.ImageID)],
                          field=self.fields[str(row.FieldID)])


class MigrateUserSystemPermissions(MigrateModel):

    def __init__(self, cursor):
        super(MigrateUserSystemPermissions, self).__init__(
            cursor=cursor,
            model=User,
            m2m_model=Permission,
            type='system',
            label='User System Permissions',
            query="SELECT UserID FROM accesscontrol WHERE ObjectType='O' "
            "AND ObjectID=1 AND UserID>0 AND GrantPriv&%s=%s "
            "AND DenyPriv&%s=0" % (
                  P['PublishSlideshow'],
                  P['PublishSlideshow'],
                  P['PublishSlideshow']
            )
        )
        self.users = MigrateModel.instance_maps['user']
        self.publish_permission = Permission.objects.get(
            codename='publish_presentations')

    def key(self, row):
        return str(row.UserID)

    def m2m_create(self, row):
        user = self.users.get(str(row.UserID))
        if user:
            user.user_permissions.add(self.publish_permission)
            return user.id, self.publish_permission.id
        else:
            return None, None

    def m2m_delete(self, object_id, m2m_object_id):
        try:
            User.objects.get(id=object_id).user_permissions.remove(
                Permission.objects.get(id=m2m_object_id))
        except Permission.DoesNotExist:
            pass
        except User.DoesNotExist:
            pass


class MigrateUserGroupSystemPermissions(MigrateModel):

    def __init__(self, cursor):
        super(MigrateUserGroupSystemPermissions, self).__init__(
            cursor=cursor,
            model=Group,
            m2m_model=Permission,
            type='system',
            label='User System Permissions',
            query="SELECT GroupID FROM accesscontrol WHERE ObjectType='O' "
            "AND ObjectID=1 AND GroupID>0 AND GrantPriv&%s=%s "
            "AND DenyPriv&%s=0" % (
                P['PublishSlideshow'],
                P['PublishSlideshow'],
                P['PublishSlideshow']
            )
        )
        self.usergroups = MigrateModel.instance_maps['group']
        self.publish_permission = Permission.objects.get(
            codename='publish_presentations')

    def key(self, row):
        return str(row.GroupID)

    def m2m_create(self, row):
        usergroup = self.usergroups.get(str(row.GroupID))
        if usergroup:
            usergroup.permissions.add(self.publish_permission)
            return usergroup.id, self.publish_permission.id
        else:
            return None, None

    def m2m_delete(self, object_id, m2m_object_id):
        try:
            Group.objects.get(id=object_id).permissions.remove(
                Permission.objects.get(id=m2m_object_id))
        except Permission.DoesNotExist:
            pass
        except User.DoesNotExist:
            pass


class MigratePermissions(MigrateModel):

    def __init__(self, cursor, type, code, instances, query=None, label=None):
        if not query:
            query = "SELECT ID,ObjectID,UserID,GroupID,GrantPriv,DenyPriv " \
            "FROM accesscontrol WHERE ObjectType='%s' AND ObjectID>0" % code
        super(MigratePermissions, self).__init__(
            cursor=cursor,
            model=AccessControl,
            type=type,
            query=query,
            label=label
        )
        self.users = MigrateModel.instance_maps['user']
        self.user_groups = MigrateModel.instance_maps['group']
        self.instances = MigrateModel.instance_maps[instances]

    def populate_ac(self, ac, row, readmask, writemask, managemask,
                    restrictions_callback=None):

        def tristate(mask):
            if row.DenyPriv and row.DenyPriv & mask:
                return False
            if row.GrantPriv and row.GrantPriv & mask:
                return True
            return None

        ac.read = tristate(readmask)
        ac.write = tristate(writemask)
        ac.manage = tristate(managemask)
        if row.UserID and str(row.UserID) in self.users:
            ac.user = self.users[str(row.UserID)]
        elif str(row.GroupID) in self.user_groups:
            ac.usergroup = self.user_groups[str(row.GroupID)]
        elif row.UserID == -1:
            pass
        else:
            return False
        if restrictions_callback:
            restrictions_callback(ac, row)
        return True

    def hash(self, row):
        return content_hash(row.ObjectID, row.UserID, row.GroupID,
                            row.GrantPriv, row.DenyPriv)

    def create_instance(self, row):
        if str(row.ObjectID) not in self.instances:
            return None
        return AccessControl()


class MigrateSlideshowPermissions(MigratePermissions):

    def __init__(self, cursor):
        super(MigrateSlideshowPermissions, self).__init__(
            cursor=cursor,
            type='pres',
            code='S',
            instances='presentation',
            label='Slideshow Permissions'
        )

    def update(self, instance, row):
        instance.content_object = self.instances[str(row.ObjectID)]
        # Privilege.ModifyACL -> n/a
        # Privilege.ModifySlideshow -> write
        # Privilege.DeleteSlideshow -> manage
        # Privilege.ViewSlideshow -> read
        # Privilege.CopySlideshow -> n/a
        if not self.populate_ac(
                instance, row, P['ViewSlideshow'],
                P['ModifySlideshow'], P['DeleteSlideshow']):
            raise IntegrityError()


class MigrateCollectionPermissions(MigratePermissions):

    def __init__(self, cursor):
        super(MigrateCollectionPermissions, self).__init__(
            cursor=cursor,
            type='coll',
            code='C',
            instances='collection',
            label='Collection Permissions'
        )

    def update(self, instance, row):
        instance.content_object = self.instances[str(row.ObjectID)]
        if not self.populate_ac(
                instance, row, P['ReadCollection'], P['ModifyImages'],
                P['ManageCollection']):
            raise IntegrityError()


class MigrateStoragePermissions(MigratePermissions):

    def __init__(self, cursor):
        query = "SELECT accesscontrol.ID,ObjectID,UserID,accesscontrol." \
            "GroupID,GrantPriv,DenyPriv,MediumImageHeight,MediumImageWidth " \
            "FROM accesscontrol INNER JOIN collections " \
            "ON ObjectID=collections.ID WHERE ObjectType='C' AND ObjectID>0"
        super(MigrateStoragePermissions, self).__init__(
            cursor=cursor,
            type='stor',
            code='C',
            instances='storage',
            query=query,
            label='Storage Permissions'
        )

    def hash(self, row):
        return content_hash(
            row.ObjectID, row.UserID, row.GroupID, row.GrantPriv,
            row.DenyPriv, row.MediumImageHeight, row.MediumImageWidth)

    def update(self, instance, row):
        instance.content_object = self.instances[str(row.ObjectID)]

        def general_restrictions(ac, row):
            full_access = row.GrantPriv and \
                row.GrantPriv & P['FullSizedImages']
            if instance.read and not full_access:
                instance.restrictions = dict(
                    height=row.MediumImageHeight,
                    width=row.MediumImageWidth
                )

        if not self.populate_ac(
                instance, row, P['ReadCollection'],
                P['ModifyImages'] | P['PersonalImages'],
                P['ManageCollection'], general_restrictions):
            raise IntegrityError()


class MigrateVocabularyPermissions(MigratePermissions):

    def __init__(self, cursor):
        query = "SELECT accesscontrol.ID,UserID,GroupID,GrantPriv,DenyPriv," \
            "controlledlists.ID as ObjectID FROM accesscontrol " \
            "INNER JOIN controlledlists ON " \
            "ObjectID=controlledlists.CollectionID " \
            "WHERE ObjectType='C' AND ObjectID>0"
        super(MigrateVocabularyPermissions, self).__init__(
            cursor=cursor,
            type='vocab',
            code='C',
            instances='vocabulary',
            query=query,
            label='Vocabulary Permissions'
        )

    def update(self, instance, row):
        instance.content_object = self.instances[str(row.ObjectID)]
        if not self.populate_ac(
                instance, row, P['ReadCollection'], P['ManageControlledLists'],
                P['ManageControlledLists']):
            raise IntegrityError()


class Command(BaseCommand):
    help = 'Migrates database from MDID2'

    def add_arguments(self, parser):
        parser.add_argument('config_file',
                            help='Path to MDID2 config.xml file')

        parser.add_argument(
            '--remove-full-prefix',
            dest='remove_full_prefix',
            action='store_true',
            help='Remove full/ prefix from media paths'
        )

    def read_config(self, file):
        connection = servertype = None
        for e in minidom.parse(
                file).getElementsByTagName('database')[0].childNodes:
            if e.localName == 'connection':
                connection = e.firstChild.nodeValue
            elif e.localName == 'servertype':
                servertype = e.firstChild.nodeValue
        return (servertype, connection)

    def handle(self, *args, **options):

        logging.info("Starting migration")

        config_file = options['config_file']
        servertype, connection = self.read_config(config_file)

        def get_cursor():
            if servertype == "MSSQL":
                conn = pyodbc.connect('DRIVER={SQL Server};%s' % connection)
            elif servertype == "MYSQL":
                conn = pyodbc.connect('DRIVER={MySQL};%s' % connection)
            elif servertype == "CUSTOM":
                conn = pyodbc.connect(connection)
            else:
                print("Unsupported database type")
                return None
            return conn.cursor()

        row = get_cursor().execute(
            "SELECT Version FROM databaseversion").fetchone()
        supported = ("00006", "00007", "00008")
        if row.Version not in supported:
            print("Database version is not supported")
            print("Found %r, supported is %r" % (row.Version, supported))
            return

        MigrateMedia.remove_full_prefix = options.get('remove_full_prefix')

        import rooibos.solr.models
        rooibos.solr.models.SolrIndexUpdates.objects.all().delete()
        rooibos.solr.models.disconnect_signals()

        migrations = [
            MigrateUsers,
            MigrateCollectionGroups,
            MigrateCollections,
            MigrateRecords,
            MigratePresentations,
            MigratePresentationItems,
            MigrateGroups,
            MigrateSubnet,
            MigrateAttribute,
            MigrateMembers,
            MigrateStorages,
            MigrateFieldSets,
            MigrateCollectionParents,
            MigrateRecordSuggestions,
            MigrateControlledLists,
            MigrateControlledListItems,
            MigrateFavoriteImages,
            MigrateImageNotes,
            MigratePresentationFolders,
            MigrateFields,
            MigrateEquivalentFields,
            MigrateFieldSetFields,
            MigrateUserSystemPermissions,
            MigrateUserGroupSystemPermissions,
            MigrateSlideshowPermissions,
            MigrateCollectionPermissions,
            MigrateStoragePermissions,
            MigrateVocabularyPermissions,
            MigrateCollectionItems,
            MigrateMedia,
            MigrateFieldValues,
        ]

        for i, m in enumerate(migrations):
            m(get_cursor()).run(step=i + 1, steps=len(migrations))

        print("You must now run 'manage.py solr reindex' to rebuild " \
            "the full-text index.")
