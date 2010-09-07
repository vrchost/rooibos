from datetime import datetime
import re
from threading import Thread
from django.conf import settings
from django.db.models import Q
from django.db import reset_queries
from django.contrib.contenttypes.models import ContentType
from rooibos.data.models import Record, Collection, Field, FieldValue, CollectionItem
from rooibos.storage.models import Media
from rooibos.util.models import OwnedWrapper
from rooibos.contrib.tagging.models import Tag, TaggedItem
from pysolr import Solr
from rooibos.util.progressbar import ProgressBar

SOLR_EMPTY_FIELD_VALUE = 'unspecified'

class SolrIndex():
    
    def __init__(self):
        self._clean_string_re = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')
        self._record_type = int(ContentType.objects.get_for_model(Record).id)
    
    def search(self, q, sort=None, start=None, rows=None, facets=None, facet_limit=-1, facet_mincount=0, fields=None):
        if not fields:
            fields = ['id']
        elif not 'id' in fields:
            fields.append('id')
        conn = Solr(settings.SOLR_URL)
        result = conn.search(q, sort=sort, start=start, rows=rows,
                             facets=facets, facet_limit=facet_limit, facet_mincount=facet_mincount, fields=fields)
        ids = [int(r['id']) for r in result]
        records = Record.objects.in_bulk(ids)
        return (result.hits, filter(None, map(lambda i: records.get(i), ids)), result.facets)
        
    def clear(self):
        from models import SolrIndexUpdates
        SolrIndexUpdates.objects.filter(delete=True).delete()
        conn = Solr(settings.SOLR_URL)
        conn.delete(q='*:*')        
        
    def optimize(self):
        conn = Solr(settings.SOLR_URL)
        conn.optimize()
    
    def index(self, verbose=False, all=False):
        from models import SolrIndexUpdates
        self._build_group_tree()
        conn = Solr(settings.SOLR_URL)
        core_fields = dict((f, f.get_equivalent_fields()) for f in Field.objects.filter(standard__prefix='dc'))
        count = 0
        batch_size = 500
        process_thread = None
        if all:
            total_count = Record.objects.count()            
        else:
            processed_updates = []
            to_update = []
            to_delete = []
            for id,record,delete in SolrIndexUpdates.objects.all()[:batch_size].values_list('id', 'record', 'delete'):
                processed_updates.append(id)
                if delete:
                    to_delete.append(record)
                else:
                    to_update.append(record)
            if to_delete:
                conn.delete(q='id:(%s)' % ' '.join(map(str, to_delete)))
            total_count = len(to_update)
                
        if verbose: pb = ProgressBar(total_count)
        while True:
            if verbose: pb.update(count)
            if all:
                records = Record.objects.all()[count:count + batch_size]
            else:
                records = Record.objects.filter(id__in=to_update)[count:count + batch_size]
            if not records:
                break
            media_dict = self._preload_related(Media, records)
            fieldvalue_dict = self._preload_related(FieldValue, records, related=2)
            groups_dict = self._preload_related(CollectionItem, records)
            count += len(records)
            
            def process_data(groups, fieldvalues, media):
                def process():
                    docs = []
                    for record in records:
                        docs += [self._record_to_solr(record, core_fields, groups.get(record.id, []),
                                                      fieldvalues.get(record.id, []), media.get(record.id, []))]
                    conn.add(docs)                
                return process
                
            if process_thread:
                process_thread.join()
            process_thread = Thread(target=process_data(groups_dict, fieldvalue_dict, media_dict))
            process_thread.start()
            reset_queries()

        if process_thread:
            process_thread.join()    
        if verbose: pb.done()
        
        if all:
            SolrIndexUpdates.objects.filter(delete=False).delete()
        else:
            SolrIndexUpdates.objects.filter(id__in=processed_updates).delete()
    
    @staticmethod
    def mark_for_update(record_id, delete=False):
        from models import mark_for_update
        mark_for_update(record_id, delete)
    
    def _preload_related(self, model, records, filter=Q(), related=0):
        dict = {}
        for x in model.objects.select_related(depth=related).filter(filter, record__in=records):
            dict.setdefault(x.record_id, []).append(x)
        return dict
    
    def _record_to_solr(self, record, core_fields, groups, fieldvalues, media):
        required_fields = dict((f.name, None) for f in core_fields.keys())
        doc = { 'id': str(record.id) }        
        for v in fieldvalues:
            clean_value = self._clean_string(v.value)
            # Store Dublin Core or equivalent field for use with facets
            for cf, cfe in core_fields.iteritems():
                if v.field == cf or v.field in cfe:
                    doc.setdefault(cf.name + '_t', []).append(clean_value)
                    if not doc.has_key(cf.name + '_sort'):
                        doc[cf.name + '_sort'] = clean_value
                    required_fields.pop(cf.name, None)
                    break
            else:
                doc.setdefault(v.field.name + '_t', []).append(clean_value)
            # For exact retrieval through browsing
            doc.setdefault(v.field.full_name + '_s', []).append(clean_value)
        for f in required_fields:
            doc[f + '_t'] = SOLR_EMPTY_FIELD_VALUE
        all_parents = [g.collection_id for g in groups]
        parents = [g.collection_id for g in groups if not g.hidden]
        # Combine the direct parents with (great-)grandparents
        doc['collections'] = list(reduce(lambda x, y: set(x) | set(y), [self.parent_groups[p] for p in parents], parents))
        doc['allcollections'] = list(reduce(lambda x, y: set(x) | set(y), [self.parent_groups[p] for p in all_parents], all_parents))
        if record.owner_id:
            doc['owner'] = record.owner_id
        for m in media:
            doc.setdefault('mimetype', []).append('s%s-%s' % (m.storage_id, m.mimetype))
            doc.setdefault('resolution', []).append('s%s-%s' % (m.storage_id, self._determine_resolution_label(m.width, m.height)))
        # Index tags
        for ownedwrapper in OwnedWrapper.objects.select_related('user').filter(content_type=self._record_type, object_id=record.id):
            for tag in ownedwrapper.taggeditem.select_related('tag').all().values_list('tag__name', flat=True):
                doc.setdefault('tag', []).append(tag)
                doc.setdefault('ownedtag', []).append('%s-%s' % (ownedwrapper.user.id, tag))
        return doc    
    
    def _clean_string(self, s):
        return self._clean_string_re.sub(' ', s)
    
    def _determine_resolution_label(self, width, height):
        sizes = ((2400, 'large'), (1600, 'moderate'), (800, 'medium'), (400, 'small'),)
        r = max(width, height)
        if not r: return 'unknown'
        for s, t in sizes:
            if r >= s: return t
        return 'tiny'
    
    # A record in a collection also belongs to all parent groups
    # This method builds a simple lookup table to quickly find all parent groups
    def _build_group_tree(self):
        self.parent_groups = {}
        for collection in Collection.objects.all():
            self.parent_groups[collection.id] = [g.id for g in collection.all_parent_collections]

