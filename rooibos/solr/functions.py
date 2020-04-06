import re
from threading import Thread
from django.conf import settings
from django.db.models import Q, Min
from django.db import reset_queries
from django.contrib.contenttypes.models import ContentType
from rooibos.data.models import Record, Collection, Field, FieldValue, \
    CollectionItem, standardfield, get_system_field
from rooibos.storage.models import Media
from rooibos.util.models import OwnedWrapper
from .pysolr import Solr
from rooibos.util.progressbar import ProgressBar
from rooibos.access.models import AccessControl
import logging
import sys
from functools import reduce


logger = logging.getLogger(__name__)


class PrimaryWorkRecordManager(object):

    def __init__(self):
        self._works_with_primary_records = None

    def _fetch_works_with_primary_records(self):
        if self._works_with_primary_records is not None:
            return

        records = FieldValue.objects.filter(
            field=get_system_field(),
            label='primary-work-record',
        ).values('record')

        # works that have primary records
        self._works_with_primary_records = set(
            FieldValue.objects.filter(
                field__standard__prefix='dc',
                field__name='relation',
                refinement='IsPartOf',
                record__in=records,
            ).distinct().order_by().values_list('value', flat=True)
        )

    def _works_for_records(self, record_ids):
        return set(
            FieldValue.objects.filter(
                field__standard__prefix='dc',
                field__name='relation',
                refinement='IsPartOf',
                record__in=record_ids,
            ).distinct().order_by().values_list('value', flat=True)
        )

    def get_implicit_primary_work_records(self, record_ids):
        self._fetch_works_with_primary_records()
        works_without_primary_records = (
            self._works_for_records(record_ids) -
            self._works_with_primary_records
        )

        # get records for works without primary records
        primary_records = FieldValue.objects.filter(
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
            value__in=works_without_primary_records,
            index_value__in=(v[:32] for v in works_without_primary_records),
        ).order_by().values('value').annotate(Min('record'))

        return set(pr['record__min'] for pr in primary_records)


SOLR_EMPTY_FIELD_VALUE = 'unspecified'


def object_acl_to_solr(obj):
    content_type = ContentType.objects.get_for_model(obj)
    acl = AccessControl.objects.filter(
        content_type=content_type,
        object_id=obj.id,
    ).values_list('user_id', 'usergroup_id', 'read', 'write', 'manage')
    result = dict(read=[], write=[], manage=[])
    for user, group, read, write, manage in acl:
        acct = 'u%d' % user if user else 'g%d' % group if group else 'anon'
        if read is not None:
            result['read'].append(acct if read else acct.upper())
        if write is not None:
            result['write'].append(acct if write else acct.upper())
        if manage is not None:
            result['manage'].append(acct if manage else acct.upper())
    if not result['read']:
        result['read'].append('default')
    if not result['write']:
        result['write'].append('default')
    if not result['manage']:
        result['manage'].append('default')
    return result


class SolrIndex():

    def __init__(self):
        self._clean_string_re = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')
        self._record_type = int(ContentType.objects.get_for_model(Record).id)
        self.system_field = get_system_field()

    def search(self, q, sort=None, start=None, rows=None, facets=None,
               facet_limit=-1, facet_mincount=0, fields=None):
        if not fields:
            fields = []
        if 'id' not in fields:
            fields.append('id')
        if 'presentations' not in fields:
            fields.append('presentations')
        conn = Solr(settings.SOLR_URL)
        result = conn.search(q, sort=sort, start=start, rows=rows,
                             facets=facets, facet_limit=facet_limit,
                             facet_mincount=facet_mincount, fields=fields)
        ids = [int(r['id']) for r in result]
        records = Record.objects.in_bulk(ids)
        for r in result:
            record = records.get(int(r['id']))
            presentations = r.get('presentations')
            if record and presentations:
                record.solr_presentation_ids = presentations
        return (result.hits, [_f for _f in [records.get(i) for i in ids] if _f],
                result.facets)

    def terms(self):
        conn = Solr(settings.SOLR_URL)
        return conn.terms(
            fields=['text'], mincount=2, minlength=4).get('text', {})

    def clear(self):
        from .models import SolrIndexUpdates
        SolrIndexUpdates.objects.filter(delete=True).delete()
        conn = Solr(settings.SOLR_URL)
        conn.delete(q='*:*')

    def optimize(self):
        conn = Solr(settings.SOLR_URL)
        conn.optimize()

    def index(self, verbose=False, all=False, collections=None):
        from .models import SolrIndexUpdates
        self._build_group_tree()
        core_fields = dict(
            (f, f.get_equivalent_fields())
            for f in Field.objects.filter(standard__prefix='dc')
        )
        # add VRA Title to support work titles
        try:
            vra_title = Field.objects.get(name='title', standard__prefix='vra')
            core_fields[vra_title] = vra_title.get_equivalent_fields()
        except Field.DoesNotExist:
            pass
        count = 0
        batch_size = 100
        process_thread = None
        if all:
            query = Record.objects.all()
            if collections:
                query = query.filter(collection__in=collections)
            total_count = query.count()
            to_update = None
            to_delete = None
        else:
            processed_updates = []
            to_update = []
            to_delete = []
            updates = SolrIndexUpdates.objects.all()[:batch_size].values_list(
                'id', 'record', 'delete')
            for id, record, delete in updates:
                processed_updates.append(id)
                if delete:
                    to_delete.append(record)
                else:
                    to_update.append(record)
            total_count = len(to_update)

        if not all and not to_update and not to_delete:
            logger.info("Nothing to update in index, returning early")
            return 0

        conn = Solr(settings.SOLR_URL)
        if to_delete:
            conn.delete(q='id:(%s)' % ' '.join(map(str, to_delete)))

        primary_work_record_manager = PrimaryWorkRecordManager()

        if verbose:
            pb = ProgressBar(total_count)

        def get_method(method):
            module, _, function = method.rpartition('.')
            try:
                __import__(module)
                mod = sys.modules[module]
                return getattr(mod, function)
            except Exception as ex:
                logging.debug(
                    "Could not import custom Solr record indexer %s: %s",
                    method, ex)

        def get_custom_doc_processor():
            method = getattr(settings, 'SOLR_RECORD_INDEXER', None)
            if method:
                method = get_method(method)
            return method or (lambda doc, **kwargs: doc)

        def get_custom_doc_pre_processor():
            method = getattr(settings, 'SOLR_RECORD_PRE_INDEXER', None)
            if method:
                method = get_method(method)
            return method or (lambda **kwargs: None)

        custom_doc_processor = get_custom_doc_processor()
        custom_doc_pre_processor = get_custom_doc_pre_processor()

        while True:
            if verbose:
                pb.update(count)
            if all:
                records = Record.objects.all()
                if collections:
                    records = records.filter(collection__in=collections)
            else:
                records = Record.objects.filter(id__in=to_update)
            records = records[count:count + batch_size]
            record_ids = records.values_list('id', flat=True)
            if not record_ids:
                break
            # convert to plain list, because Django's value lists will add a
            # LIMIT clause when used in an __in query, which causes MySQL to
            # break.  (ph): also, made an explicit separate value for this
            record_id_list = list(record_ids)
            media_dict = self._preload_related(Media, record_id_list)
            fieldvalue_dict = self._preload_related(FieldValue, record_id_list,
                                                    fields=('field',))
            groups_dict = self._preload_related(CollectionItem, record_id_list)

            image_to_works = self._preload_image_to_works(record_id_list)
            work_to_images = self._preload_work_to_images(record_id_list)

            implicit_primary_work_records = primary_work_record_manager \
                .get_implicit_primary_work_records(record_id_list)

            count += len(record_id_list)

            # VERY IMPORTANT:  SINCE process_data RUNS IN ANOTHER THREAD, IT
            # CANNOT DIRECTLY ACCESS ANY VARIABLES FROM THE OUTER SCOPE
            # ALWAYS PASS IN ANY NEEDED VARIABLES

            def process_data(groups, fieldvalues, media, record_id_list,
                             image_to_works, work_to_images,
                             implicit_primary_work_records):
                def process():
                    docs = []
                    for record in Record.objects.filter(id__in=record_id_list):
                        g = groups.get(record.id, [])
                        fv = fieldvalues.get(record.id, [])
                        m = media.get(record.id, [])
                        custom_doc_pre_processor(
                            record=record,
                            core_fields=core_fields,
                            groups=g,
                            fieldvalues=fv,
                            media=m,
                        )
                        doc = self._record_to_solr(
                            record, core_fields, g, fv, m,
                            image_to_works,
                            work_to_images,
                            implicit_primary_work_records
                        )
                        doc = custom_doc_processor(
                            doc,
                            record=record,
                            core_fields=core_fields,
                            groups=g,
                            fieldvalues=fv,
                            media=m,
                        )
                        docs.append(doc)
                    conn.add(docs)
                return process

            if process_thread:
                process_thread.join()
            process_thread = Thread(
                target=process_data(groups_dict, fieldvalue_dict,
                                    media_dict, record_id_list,
                                    image_to_works, work_to_images,
                                    implicit_primary_work_records))
            process_thread.start()
            reset_queries()

        if process_thread:
            process_thread.join()
        if verbose:
            pb.done()

        if all:
            # TODO: this will remove objects that have been added
            # in the meantime
            SolrIndexUpdates.objects.filter(delete=False).delete()
        else:
            SolrIndexUpdates.objects.filter(id__in=processed_updates).delete()

        return count

    def clear_missing(self, verbose=False):
        conn = Solr(settings.SOLR_URL)
        start = 0
        to_delete = []
        pb = None
        if verbose:
            print("Checking for indexed records no longer in database")
        while True:
            if verbose and pb:
                pb.update(start)
            result = conn.search('*:*', sort='id asc', start=start, rows=500,
                                 fields=['id'])
            if not result:
                break
            if verbose and not pb:
                pb = ProgressBar(result.hits)
            ids = [int(r['id']) for r in result]
            records = Record.objects.filter(id__in=ids).values_list('id',
                                                                    flat=True)
            for r in records:
                ids.remove(r)
            to_delete.extend(ids)
            start += 500
        if verbose and pb:
            pb.done()
        pb = None
        if verbose and to_delete:
            print("Removing unneeded records from index")
            pb = ProgressBar(len(to_delete))
        while to_delete:
            if verbose and pb:
                pb.update(pb.total - len(to_delete))
            conn.delete(q='id:(%s)' % ' '.join(map(str, to_delete[:500])))
            to_delete = to_delete[500:]
        if verbose and pb:
            pb.done()

    @staticmethod
    def mark_for_update(record_id, delete=False):
        from .models import mark_for_update
        mark_for_update(record_id, delete)

    def _preload_related(self, model, record_ids, filter=Q(), fields=None):
        d = dict((i, []) for i in record_ids)
        fields = fields or []
        for x in model.objects.select_related(*fields).filter(
                filter, record__id__in=record_ids):
            d[x.record_id].append(x)
        return d

    def _preload_image_to_works(self, record_ids):

        image_to_works = dict()

        work_relation = FieldValue.objects.filter(
            record__in=record_ids,
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
        ).values_list('record__id', 'value')

        works = FieldValue.objects.filter(
            field__in=standardfield('identifier', equiv=True),
            value__in=(wr[1] for wr in work_relation),
            index_value__in=(wr[1][:32] for wr in work_relation),
        ).values_list('value', 'record__id')
        works = dict(works)

        for record_id, work in work_relation:
            work_id = works.get(work)
            if work_id:
                image_to_works.setdefault(record_id, []).append(work_id)

        return image_to_works

    def _preload_work_to_images(self, record_ids):

        q = Q(
            field__in=standardfield('identifier', equiv=True),
        ) | Q(
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
        )

        identifiers = FieldValue.objects.filter(
            q,
            record__in=record_ids,
        ).values_list('value', 'record__id')

        images = FieldValue.objects.filter(
            field__standard__prefix='dc',
            field__name='relation',
            refinement='IsPartOf',
            value__in=(i[0] for i in identifiers),
            index_value__in=(i[0][:32] for i in identifiers),
        )
        images = images.values_list('record__id', 'value')

        identifier_map = dict()
        for v, r in identifiers:
            identifier_map.setdefault(v, []).append(r)

        work_to_images = dict()
        for record_id, image in images:
            image_ids = identifier_map.get(image, [])
            for i in image_ids:
                if record_id != i:
                    work_to_images.setdefault(i, []).append(record_id)

        return work_to_images

    def _record_to_solr(self, record, core_fields, groups, fieldvalues, media,
                        image_to_works, work_to_images,
                        implicit_primary_work_records):
        required_fields = dict((f.full_name, f) for f in list(core_fields.keys()))
        doc = {'id': str(record.id)}
        for v in fieldvalues:
            clean_value = self._clean_string(v.value)
            # Store Dublin Core or equivalent field for use with facets
            for cf, cfe in core_fields.items():
                name = cf.name if cf.standard.prefix == 'dc' else cf.full_name
                if v.field == cf or v.field in cfe:
                    doc.setdefault(name + '_t', []).append(clean_value)
                    doc.setdefault(name + '_w', []).append(clean_value)
                    if not name + '_sort' in doc:
                        doc[name + '_sort'] = clean_value
                    required_fields.pop(cf.full_name, None)
                    if v.refinement:
                        doc.setdefault(
                            name + '.' + v.refinement + '_t', []
                        ).append(clean_value)
                        if v.refinement.lower() == 'ispartof':
                            doc.setdefault('work', []).append(clean_value)
                    break
            else:
                if (v.field == self.system_field and
                        v.label == 'primary-work-record'):
                    doc.setdefault(
                        'primary_work_record', []
                    ).append(v.value)
                else:
                    doc.setdefault(v.field.name + '_t', []).append(clean_value)
                    doc.setdefault(v.field.name + '_w', []).append(clean_value)
                    # also make sortable
                    if not v.field.name + '_sort' in doc:
                        doc[v.field.name + '_sort'] = clean_value
            # For exact retrieval through browsing
            doc.setdefault(v.field.full_name + '_s', []).append(clean_value)
        for _, f in list(required_fields.items()):
            doc[f.name + '_t'] = SOLR_EMPTY_FIELD_VALUE
        all_parents = [g.collection_id for g in groups]
        parents = [g.collection_id for g in groups if not g.hidden]
        # Combine the direct parents with (great-)grandparents
        # 'collections' is used for access control,
        # hidden collections deny access
        doc['collections'] = list(
            reduce(lambda x, y: set(x) | set(y),
                   [self.parent_groups[p] for p in parents], parents))
        # 'allcollections' is used for collection filtering,
        # can filter by hidden collections
        doc['allcollections'] = list(
            reduce(lambda x, y: set(x) | set(y),
                   [self.parent_groups[p] for p in all_parents], all_parents))
        presentations = record.presentationitem_set.all().distinct()
        doc['presentations'] = presentations.values_list('presentation_id',
                                                         flat=True)
        if record.owner_id:
            doc['owner'] = record.owner_id
        for m in media:
            doc.setdefault('mimetype', []).append(
                's%s-%s' % (m.storage_id, m.mimetype))
            doc.setdefault('resolution', []).append(
                's%s-%s' % (
                    m.storage_id,
                    self._determine_resolution_label(m.width, m.height)))
            try:
                doc.setdefault('filecontent', []).append(m.extract_text())
            except:
                pass
        # Index tags
        for ownedwrapper in OwnedWrapper.objects.select_related('user').filter(
                content_type=self._record_type, object_id=record.id):
            for tag in ownedwrapper.taggeditem.select_related(
                    'tag').all().values_list('tag__name', flat=True):
                doc.setdefault('tag', []).append(tag)
                doc.setdefault('ownedtag', []).append(
                    '%s-%s' % (ownedwrapper.user.id, tag))
        # Creation and modification dates
        doc['created'] = record.created
        doc['modified'] = record.modified
        # Access control
        acl = object_acl_to_solr(record)
        doc['acl_read'] = acl['read']
        doc['acl_write'] = acl['write']
        doc['acl_manage'] = acl['manage']
        # Work-Image relations
        i2w = image_to_works.get(record.id, [])
        doc['related_works_count'] = len(i2w)
        w2i = work_to_images.get(record.id, [])
        doc['related_images_count'] = len(w2i)

        if record.id in implicit_primary_work_records:
            doc.setdefault(
                'primary_work_record', []
            ).append('Yes')

        return doc

    def _clean_string(self, s):
        return self._clean_string_re.sub(' ', s)

    def _determine_resolution_label(self, width, height):
        sizes = (
            (2400, 'large'),
            (1600, 'moderate'),
            (800, 'medium'),
            (400, 'small'),
        )
        r = max(width, height) if width and height else None
        if not r:
            return 'unknown'
        for s, t in sizes:
            if r >= s:
                return t
        return 'tiny'

    # A record in a collection also belongs to all parent groups
    # This method builds a simple lookup table to quickly find
    # all parent groups
    def _build_group_tree(self):
        self.parent_groups = {}
        for collection in Collection.objects.all():
            self.parent_groups[collection.id] = [
                g.id for g in collection.all_parent_collections
            ]
