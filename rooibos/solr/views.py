from django.db.models import Count
from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django import forms
from django.forms.formsets import formset_factory
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .functions import SolrIndex
from .pysolr import SolrError
from rooibos.access.functions import filter_by_access
import socket
from rooibos.util import safe_int, json_view, calculate_hash
from rooibos.data.models import Field, Collection, FieldValue, Record, \
    FieldSet, FieldSetField, get_system_field
from rooibos.data.functions import apply_collection_visibility_preferences, \
    get_collection_visibility_preferences
from rooibos.storage.models import Storage
from rooibos.ui import update_record_selection, clean_record_selection_vars
from rooibos.federatedsearch.views import sidebar_api_raw, \
    available_federated_sources
import re
import copy
import random
import logging
from datetime import datetime
from functools import reduce, cmp_to_key

logger = logging.getLogger(__name__)


class SearchFacet(object):

    def __init__(self, name, label):
        self.name = name
        self.label = label

    def process_criteria(self, criteria, *args, **kwargs):
        return criteria

    def set_result(self, facets):
        # break down dicts into tuples
        if hasattr(facets, 'items'):
            self.facets = list(facets.items())
        else:
            self.facets = facets

    def clean_result(self, hits, sort=True):
        # sort facet items and remove the ones that match all hits
        facets = getattr(self, 'facets', None) or []
        self.facets = [f for f in facets if f[1] is not None and f[1] < hits]
        if sort:
            self.facets = sorted(self.facets,
                             key=lambda f: f[2 if len(f) > 2 else 0])

    def or_available(self):
        return True

    def display_value(self, value):
        return value.replace('|', ' or ')

    def federated_search_query(self, value):
        return value.replace('|', ' ')

    def fetch_facet_values(self):
        return True


class WorkSearchFacet(SearchFacet):

    def process_criteria(self, criteria, *args, **kwargs):
        return '|'.join(
            '"' + _special.sub(r'\\\1', _strip_quotes.sub(r'\1', c)) + '"'
            for c in criteria.split('|')
        )

    def display_value(self, value):
        values = value.split('|')
        comment = ''
        if len(values) > 1:
            comment = (' (+%d others)' % (len(values) - 1))
        for v in values:
            record = Record.get_primary_work_record(v)
            if record:
                title = record.work_title or record.title
                if title:
                    return title + comment
        return value


class RecordDateSearchFacet(SearchFacet):

    def or_available(self):
        return False

    def federated_search_query(self, value):
        return ''

    def display_value(self, value):
        match = re.match(r'\[NOW-(\d+)DAYS? TO \*\]', value)
        if match:
            return "Within last %s day%s" % (
                match.group(1),
                's' if int(match.group(1)) != 1 else '',
            )
        else:
            return value

    def fetch_facet_values(self):
        return False


class OwnerSearchFacet(SearchFacet):

    def display_value(self, value):
        value = '|'.join(User.objects.filter(
            id__in=value.split('|')).values_list('username', flat=True))
        return super(OwnerSearchFacet, self).display_value(value)

    def set_result(self, facets):
        self.facets = ()

    def or_available(self):
        return False

    def federated_search_query(self, value):
        return ''


class RelatedToSearchFacet(SearchFacet):

    def display_value(self, value):
        record = Record.objects.filter(id=value)
        value = record[0].title if record else value
        return super(RelatedToSearchFacet, self).display_value(value)

    def set_result(self, facets):
        self.facets = ()

    def federated_search_query(self, value):
        return ''

    def or_available(self):
        return False

    def process_criteria(self, criteria, user, *args, **kwargs):
        record = Record.objects.filter(id=criteria)
        if record:
            return '|'.join(
                map(str, record[0].presentationitem_set.all().distinct()
                    .values_list('presentation_id', flat=True)))
        else:
            return '-1'


class PrimaryWorkRecordSearchFacet(SearchFacet):

    def federated_search_query(self, value):
        return ''

    def or_available(self):
        return False


class StorageSearchFacet(SearchFacet):

    _storage_facet_re = re.compile(r'^s(\d+)-(.+)$')

    def __init__(self, name, label, available_storage):
        super(StorageSearchFacet, self).__init__(name, label)
        # if no storage available, use 'x' which should never match anything
        self.available_storage = available_storage or ['x']

    def process_criteria(self, criteria, user, *args, **kwargs):
        criteria = '|'.join('s*-%s' % s for s in criteria.split('|'))
        return user.is_superuser and criteria or '(%s) AND (%s)' % (
            ' '.join('s%s-*' % s for s in self.available_storage), criteria
        )

    def set_result(self, facets):
        result = {}
        if facets:
            for f in list(facets.keys()):
                m = StorageSearchFacet._storage_facet_re.match(f)
                if m and int(m.group(1)) in self.available_storage:
                    # make facet available, but without frequency count
                    result[m.group(2)] = None
        super(StorageSearchFacet, self).set_result(result)

    def federated_search_query(self, value):
        return ''


class CollectionSearchFacet(SearchFacet):

    def set_result(self, facets):
        result = []
        if facets:
            collections = Collection.objects.filter(
                id__in=list(map(int, list(facets.keys())))
            ).order_by('order', 'title').values_list('id', 'title')
            for id, title in collections:
                result.append((id, facets[str(id)], title))
        super(CollectionSearchFacet, self).set_result(result)

    def display_value(self, value):
        value = '|'.join(Collection.objects.filter(
            id__in=value.split('|')).values_list('title', flat=True))
        return super(CollectionSearchFacet, self).display_value(value)

    def federated_search_query(self, value):
        return ''

    # Override to not sort alphabetically
    def clean_result(self, hits):
        return super(CollectionSearchFacet, self).clean_result(
            hits, sort=False)


_special = re.compile(r'(\+|-|&&|\|\||!|\(|\)|\{|}|\[|\]|\^|"|~|\*|\?|:|\\)')
_strip_quotes = re.compile(r'^"(.*)"$')


class ExactValueSearchFacet(SearchFacet):

    def __init__(self, name):
        prefix, name = ([None] + name[:-2].split('.'))[-2:]
        try:
            if prefix:
                field = Field.objects.get(standard__prefix=prefix, name=name)
            else:
                field = Field.objects.get(standard=None, name=name)
            label = field.label
        except Field.DoesNotExist:
            logger.exception(
                'Cannot field field %r with prefix %r' % (name, prefix))
            label = 'Error'
        super(ExactValueSearchFacet, self).__init__(name, label)

    def process_criteria(self, criteria, *args, **kwargs):
        return '"' + _special.sub(r'\\\1', criteria) + '"'

    def or_available(self):
        return False


class OwnedTagSearchFacet(SearchFacet):

    def __init__(self):
        super(OwnedTagSearchFacet, self).__init__('ownedtag', 'Personal Tags')

    def process_criteria(self, criteria, *args, **kwargs):
        return '"' + _special.sub(r'\\\1', criteria) + '"'

    def or_available(self):
        return False

    def display_value(self, value):
        id, value = value.split('-')
        return super(OwnedTagSearchFacet, self).display_value(value)

    def federated_search_query(self, value):
        return ''


class RelatedWorksSearchFacet(SearchFacet):

    def or_available(self):
        return False

    def federated_search_query(self, value):
        return ''

    def display_value(self, value):
        return "Number of related works: %s" % value

    def fetch_facet_values(self):
        return False


class RelatedImagesSearchFacet(SearchFacet):

    def or_available(self):
        return False

    def federated_search_query(self, value):
        return ''

    def display_value(self, value):
        return "Number of related images: %s" % value

    def fetch_facet_values(self):
        return False


def _generate_query(search_facets, user, collection, criteria, keywords,
                    selected, *exclude):

    # add owned tag facet
    search_facets['ownedtag'] = OwnedTagSearchFacet()

    fields = {}
    for c in criteria:
        if (c in exclude) or (':' not in c):
            continue
        (f, o) = c.split(':', 1)
        if f.startswith('-'):
            f = 'NOT ' + f[1:]
        fname = f.rsplit(' ', 1)[-1]

        # create exact match criteria on the fly if needed
        if fname.endswith('_s') and fname not in search_facets:
            search_facets[fname] = ExactValueSearchFacet(fname)

        if fname in search_facets:
            o = search_facets[fname].process_criteria(o, user)
            fields.setdefault(f, []).append('(' + o.replace('|', ' OR ') + ')')

    fields = ['%s:(%s)' % (
            name_crit[0], (name_crit[0].startswith('NOT ') and ' OR ' or ' AND ').join(name_crit[1])) for name_crit in iter(fields.items())]

    def build_keywords(q, k):
        k = k.lower()
        if k.startswith('?') or k.startswith('*'):
            k = k[1:]
            if not k:
                return q
        if k == 'and' or k == 'or':
            return q + ' ' + k.upper()
        elif q.endswith(' AND') or q.endswith(' OR'):
            return q + ' ' + k
        else:
            return q + ' AND ' + k

    if keywords:
        keywords = re.sub('[+\\\|!()\{}\[\]^"~:]', ' ', keywords)
    if keywords:
        keywords = reduce(build_keywords, keywords.split())

    query = ''
    if fields:
        query = ' AND '.join(fields)
    if keywords:
        if query:
            query = '%s AND (%s)' % (query, keywords)
        else:
            query = '(%s)' % keywords
    if not query:
        query = '*:*'
    if collection:
        query = 'collections:%s AND %s' % (collection.id, query)
    if hasattr(selected, '__len__'):
        query = 'id:(%s) AND %s' % (
            ' '.join(map(str, selected or [-1])), query)

    if not user.is_superuser:
        collections = ' '.join(
            map(str, filter_by_access(user, Collection).values_list(
                'id', flat=True)))
        c = []
        if collections:
            # access through readable collection when no record ACL set
            c.append('collections:(%s) AND acl_read:default' % collections)
        if user.id:
            # access through ownership
            c.append('owner:%s' % user.id)
            # access through record ACL
            groups = ' '.join(
                'g%d' % id for id in user.groups.values_list('id', flat=True)
            )
            if groups:
                groups = '((%s) AND NOT (%s)) OR ' % (groups, groups.upper())
            c.append('acl_read:((%su%d) AND NOT U%d)' % (
                groups, user.id, user.id))
        else:
            # access through record ACL
            c.append('acl_read:anon')
        if c:
            query = '((%s)) AND %s' % (') OR ('.join(c), query)
        else:
            query = 'id:"-1"'

    mode, ids = get_collection_visibility_preferences(user)
    if ids:
        query += ' AND %sallcollections:(%s)' % (
            '-' if mode == 'show' else '',
            ' '.join(map(str, ids)),
        )

    return query


templates = dict(l='list', im='images')


def _get_facet_fields():
    fields = cache.get('facet_fields')
    if fields:
        fields = Field.objects.filter(id__in=fields)
    else:
        # check if fieldset for facets exists
        fieldset = None
        try:
            fieldset = FieldSet.objects.get(name='facet-fields')
        except FieldSet.DoesNotExist:
            pass
        if fieldset:
            fields = fieldset.fields.all()
        else:
            exclude_facets = ['identifier']
            fields = Field.objects.filter(standard__prefix='dc').exclude(
                name__in=exclude_facets)
        cache.set('facet_fields', [f.id for f in fields], 60)
    return fields


def run_search(user,
               collection=None,
               criteria=[],
               keywords='',
               sort='score desc',
               page=1,
               pagesize=25,
               orquery=None,
               selected=False,
               remove=None,
               produce_facets=False):

    available_storage = list(filter_by_access(user, Storage).values_list(
        'id', flat=True))

    fields = _get_facet_fields()

    full_facets = getattr(settings, 'FULL_FACETS', ())

    search_facets = [SearchFacet('tag', 'Tags')] + [
        SearchFacet(
            field.name + ('_t' if field.label not in full_facets else '_w'),
            field.label
        )
        for field in fields
    ]
    search_facets.append(
        StorageSearchFacet('resolution', 'Image size', available_storage))
    search_facets.append(
        StorageSearchFacet('mimetype', 'Media type', available_storage))
    search_facets.append(CollectionSearchFacet('allcollections', 'Collection'))
    search_facets.append(OwnerSearchFacet('owner', 'Owner'))
    search_facets.append(RelatedToSearchFacet('presentations', 'Related to'))
    search_facets.append(RecordDateSearchFacet('modified', 'Last modified'))
    search_facets.append(RecordDateSearchFacet('created', 'Record created'))
    # Image/Work facets
    search_facets.append(
        RelatedImagesSearchFacet('related_images_count', 'Images for Work'))
    search_facets.append(
        RelatedWorksSearchFacet('related_works_count', 'Works for Image'))
    search_facets.append(WorkSearchFacet('work', 'Part of Work'))
    search_facets.append(
        PrimaryWorkRecordSearchFacet(
            'primary_work_record', 'Primary Work Record'
        )
    )
    # convert to dictionary
    search_facets = dict((f.name, f) for f in search_facets)

    # check for overridden facet labels
    for name, label in (
            FieldSetField.objects.filter(fieldset__name='facet-fields')
            .exclude(label='').values_list('field__name', 'label')
    ):
        if name + '_t' in search_facets:
            search_facets[name + '_t'].label = label
        elif name + '_w' in search_facets:
            search_facets[name + '_w'].label = label

    query = _generate_query(search_facets, user, collection, criteria,
                            keywords, selected, remove)

    s = SolrIndex()

    return_facets = [key for key, facet in search_facets.items()
                     if facet.fetch_facet_values()] if produce_facets else []

    try:
        hits, records, facets = s.search(
            query, sort=sort, rows=pagesize, start=(page - 1) * pagesize,
            facets=return_facets, facet_mincount=1, facet_limit=100)
    except SolrError:
        logger.exception('SolrError: %r' % query)
        hits = -1
        records = None
        facets = dict()
    except socket.error:
        hits = 0
        records = None
        facets = dict()

    if produce_facets:
        for f in search_facets:
            search_facets[f].set_result(facets.get(f))

    if orquery:
        f, v = orquery.split(':', 1)
        orfacets = s.search(_generate_query(
            search_facets, user, collection, criteria, keywords, selected,
            remove, orquery),
            rows=0, facets=[f], facet_mincount=1, facet_limit=100)[2]
        orfacet = copy.copy(search_facets[f]) if f in search_facets else None
        if orfacet:
            orfacet.label = '%s in %s or...' % (v.replace("|", " or "),
                                                orfacet.label)
            orfacet.set_result(orfacets[f])
    else:
        orfacet = None

    return (hits, records, search_facets, orfacet, query, fields)


class DummyContent():
    def __init__(self, length):
        self.length = length
    def __len__(self):
        return self.length
    def __getitem__(self, index):
        if isinstance(index, slice):
            return list(range(index.start or 0, index.stop, index.step or 1))
        else:
            return None
    def count(self):
        return self.length


def search(request, id=None, name=None, selected=False, json=False):
    collection = get_object_or_404(
        filter_by_access(request.user, Collection), id=id) if id else None

    if request.method == "POST":
        update_record_selection(request)
        # redirect to get request with updated parameters
        q = request.GET.copy()
        q.update(request.POST)
        q = clean_record_selection_vars(q)
        for i, v in list(q.items()):
            if i != 'c':
                # replace multiple values with last one
                # except for criteria ('c')
                q[i] = v
        q.pop('v.x', None)
        q.pop('v.y', None)
        q.pop('x', None)
        q.pop('y', None)
        return HttpResponseRedirect(request.path + '?' + q.urlencode())

    # get parameters relevant for search
    criteria = request.GET.getlist('c')
    remove = request.GET.get('rem', None)
    if remove and remove in criteria:
        criteria.remove(remove)
    keywords = request.GET.get('kw', '')

    # get parameters relevant for view

    viewmode = request.GET.get('v', 'thumb')
    if viewmode == 'list':
        pagesize = max(min(safe_int(request.GET.get('ps', '50'), 50), 100), 5)
    else:
        pagesize = max(min(safe_int(request.GET.get('ps', '30'), 30), 50), 5)
    page = safe_int(request.GET.get('page', '1'), 1)
    sort = request.GET.get('s', 'title_sort').lower()
    if not sort.endswith(" asc") and not sort.endswith(" desc"):
        sort += " asc"

    orquery = request.GET.get('or', None)
    user = request.user

    if 'action' in request.GET:
        page = safe_int(request.GET.get('op', '1'), 1)

    if selected:
        selected = request.session.get('selected_records', ())

    hits, records, search_facets, orfacet, query, fields = run_search(
        user, collection, criteria, keywords, sort, page, pagesize,
        orquery, selected, remove, produce_facets=False)

    if json:
        return (hits, records, viewmode)

    if collection:
        url = reverse('solr-search-collection',
                      kwargs={'id': collection.id, 'name': collection.name})
        furl = reverse('solr-search-collection-facets',
                       kwargs={'id': collection.id, 'name': collection.name})
    elif hasattr(selected, '__len__'):
        url = reverse('solr-selected')
        furl = reverse('solr-selected-facets')
    else:
        url = reverse('solr-search')
        furl = reverse('solr-search-facets')

    q = request.GET.copy()
    q = clean_record_selection_vars(q)
    q.pop('or', None)
    q.pop('rem', None)
    q.pop('action', None)
    q.pop('page', None)
    q.pop('op', None)
    q.pop('v.x', None)
    q.pop('v.y', None)
    q.pop('x', None)
    q.pop('y', None)
    q['s'] = q.get('s', sort)
    q['v'] = q.get('v', 'thumb')
    q.setlist('c', criteria)
    hiddenfields = [('op', page)]
    qurl = q.urlencode()
    q.setlist('c', [c for c in criteria if c != orquery])
    qurl_orquery = q.urlencode()
    limit_url = "%s?%s%s" % (url, qurl, qurl and '&' or '')
    limit_url_orquery = "%s?%s%s" % (
        url, qurl_orquery, qurl_orquery and '&' or '')
    facets_url = "%s?%s%s" % (furl, qurl, qurl and '&' or '')

    form_url = "%s?%s" % (url, q.urlencode())

    prev_page_url = None
    next_page_url = None

    if page > 1:
        q['page'] = page - 1
        prev_page_url = "%s?%s" % (url, q.urlencode())
    if page < (hits - 1) // pagesize + 1:
        q['page'] = page + 1
        next_page_url = "%s?%s" % (url, q.urlencode())

    def readable_criteria(c):
        (f, o) = c.split(':', 1)
        negated = f.startswith('-')
        f = f[1 if negated else 0:]
        if f in search_facets:
            return dict(
                facet=c,
                term=search_facets[f].display_value(o),
                label=search_facets[f].label,
                negated=negated,
                or_available=not negated and search_facets[f].or_available(),
            )
        else:
            return dict(
                facet=c,
                term=o,
                label='Unknown criteria',
                negated=negated,
                or_available=False,
            )

    def reduce_federated_search_query(q, c):
        (f, o) = c.split(':', 1)
        if f.startswith('-') or f not in search_facets:
            # can't negate in federated search
            return q
        v = search_facets[f].federated_search_query(o)
        return v if not q else '%s %s' % (q, v)

    mode, ids = get_collection_visibility_preferences(user)
    hash = calculate_hash(getattr(user, 'id', 0),
                          collection,
                          criteria,
                          keywords,
                          selected,
                          remove,
                          mode,
                          str(ids),
                          )

    facets = cache.get('search_facets_html_%s' % hash)

    sort = sort.startswith('random') and 'random' or sort.split()[0]
    sort = sort.endswith('_sort') and sort[:-5] or sort

    federated_search_query = reduce(
        reduce_federated_search_query, criteria, keywords)
    federated_search = sidebar_api_raw(
        request, federated_search_query, cached_only=True
    ) if federated_search_query else None

    pagination_helper = DummyContent(hits)
    paginator = Paginator(pagination_helper, pagesize)
    page = request.GET.get('page')
    try:
        pagination_helper = paginator.page(page)
    except PageNotAnInteger:
        pagination_helper = paginator.page(1)
    except EmptyPage:
        pagination_helper = paginator.page(paginator.num_pages)

    return render(
        request,
        'results.html',
        {
            'criteria': list(map(readable_criteria, criteria)),
            'query': query,
            'keywords': keywords,
            'hiddenfields': hiddenfields,
            'records': records,
            'hits': hits,
            'page': page,
            'pages': (hits - 1) // pagesize + 1,
            'pagesize': pagesize,
            'prev_page': prev_page_url,
            'next_page': next_page_url,
            'reset_url': url,
            'form_url': form_url,
            'limit_url': limit_url,
            'limit_url_orquery': limit_url_orquery,
            'facets': facets,
            'facets_url': facets_url,
            'orfacet': orfacet,
            'orquery': orquery,
            'sort': sort,
            'random': random.random(),
            'viewmode': viewmode,
            'federated_sources': bool(
                available_federated_sources(request.user)),
            'federated_search': federated_search,
            'federated_search_query': federated_search_query,
            'pagination_helper': pagination_helper,
            'has_record_created_criteria': any(
                f.startswith('created:') for f in criteria),
            'has_last_modified_criteria': any(
                f.startswith('modified:') for f in criteria),
        }
    )


@json_view
def search_facets(request, id=None, name=None, selected=False):

    collection = get_object_or_404(
        filter_by_access(request.user, Collection), id=id) if id else None

    # get parameters relevant for search
    criteria = request.GET.getlist('c')
    remove = request.GET.get('rem', None)
    if remove and remove in criteria:
        criteria.remove(remove)
    keywords = request.GET.get('kw', '')

    user = request.user

    if selected:
        selected = request.session.get('selected_records', ())

    (hits, records, search_facets, orfacet, query, fields) = run_search(
        user, collection, criteria, keywords, selected=selected, remove=remove,
        produce_facets=True)

    if collection:
        url = reverse('solr-search-collection',
                      kwargs={'id': collection.id, 'name': collection.name})
    elif selected:
        url = reverse('solr-selected')
    else:
        url = reverse('solr-search')

    q = request.GET.copy()
    q = clean_record_selection_vars(q)
    q.pop('or', None)
    q.pop('rem', None)
    q.pop('action', None)
    q.pop('page', None)
    q.pop('op', None)
    q.setlist('c', criteria)
    qurl = q.urlencode()
    limit_url = "%s?%s%s" % (url, qurl, qurl and '&' or '')

    # sort facets by specified order, if any, then by label
    ordered_facets = (
        FieldSetField.objects
        .filter(fieldset__name='facet-fields')
        .values_list('field__name', flat=True)
        .order_by('order', 'label', 'field__label', 'field__name')
    )
    facets = []
    for of in ordered_facets:
        try:
            facets.append(search_facets.pop(of + '_t'))
        except KeyError:
            pass
    facets.extend(sorted(list(search_facets.values()), key=lambda f: f.label))

    # clean facet items
    for f in facets:
        f.clean_result(hits)

    # remove facets with only no filter options
    facets = [f for f in facets if len(f.facets) > 0]

    # remove facets that should be hidden
    hide_facets = getattr(settings, 'HIDE_FACETS', None)
    if hide_facets:
        facets = [f for f in facets if f.label not in hide_facets]

    html = render_to_string(
        'results_facets.html',
        {
            'limit_url': limit_url,
            'facets': facets
        },
        request=request)

    mode, ids = get_collection_visibility_preferences(user)
    hash = calculate_hash(getattr(user, 'id', 0),
                          collection,
                          criteria,
                          keywords,
                          selected,
                          remove,
                          mode,
                          str(ids),
                          )

    cache.set('search_facets_html_%s' % hash, html, 300)

    return dict(html=html)


@json_view
def search_json(request, id=None, name=None, selected=False):

    hits, records, viewmode = search(request, id, name, selected, json=True)

    html = render_to_string(
        'results_bare_' + templates.get(viewmode, 'icons') + '.html',
        {
            'records': records,
            'selectable': True,
        },
        request=request)

    return dict(html=html)


def _get_browse_fields(collection_id, child_collection_ids=None):
    fields = cache.get('browse_fields_%s' % collection_id)
    order = cache.get('browse_fields_order_%s' % collection_id)
    if fields and order:
        fields = list(Field.objects.filter(id__in=fields))
    else:
        # check if fieldset for browsing exists
        fieldset = None
        try:
            fieldset = FieldSet.objects.get(
                name='browse-collection-%s' % collection_id)
        except FieldSet.DoesNotExist:
            try:
                fieldset = FieldSet.objects.get(name='browse-collections')
            except FieldSet.DoesNotExist:
                pass
        collections = [collection_id]
        if child_collection_ids:
            collections.extend(child_collection_ids)
        query = FieldValue.objects.filter(record__collection__in=collections)
        if fieldset:
            query = query.filter(
                field__in=list(fieldset.fields.values_list('id', flat=True)))
        ids = list(
            query.order_by().distinct().values_list('field_id', flat=True))
        fields = list(Field.objects.filter(id__in=ids))
        # order fields by order specified in field set, if any
        if fieldset:
            order = dict(
                FieldSetField.objects.filter(fieldset=fieldset)
                    .values_list('field', 'order')
            )
        else:
            order = dict()
        cache.set('browse_fields_%s' % collection_id,
                  [f.id for f in fields], 60)
        cache.set('browse_fields_order_%s' % collection_id, order)
    fields = sorted(fields, key=lambda f: order.get(f.id, 1000000 + f.id))
    return fields


def browse(request, id=None, name=None):

    browse_children = getattr(settings, 'BROWSE_CHILDREN', False)

    collections = filter_by_access(request.user, Collection)
    collections = apply_collection_visibility_preferences(request.user,
                                                          collections)

    if not browse_children:
        # Filter out empty collections.  When browsing child collections
        # as well, we don't do this
        collections = collections.annotate(
            num_records=Count('records')).filter(
            num_records__gt=0)

    collections = collections.order_by('order', 'title')

    if not collections:
        return render(
            request,
            'browse.html'
        )

    if 'c' in request.GET:
        collection = get_object_or_404(collections, name=request.GET['c'])
        return HttpResponseRedirect(reverse(
            'solr-browse-collection',
            kwargs={'id': collection.id, 'name': collection.name}))

    fields = None
    if id:
        collection = get_object_or_404(collections, id=id)
        if collection:
            fields = _get_browse_fields(
                collection.id, list(collection.all_child_collections))
            if not fields:
                return HttpResponseRedirect(reverse('solr-browse'))

    for ic in collections:
        if fields:
            break
        collection = ic
        fields = _get_browse_fields(collection.id)

    if not fields:
        logger.debug('No browse fields found for collection %d, '
                     'invalid browse field sets?' % (collection.id,))
        raise Http404()

    collection_and_children = \
        [collection] + list(collection.all_child_collections)

    if 'f' in request.GET:
        try:
            field = get_object_or_404(Field, id=request.GET['f'],
                                      id__in=(f.id for f in fields))
        except ValueError:
            # GET['f'] was text previously and external links exist
            # that are no longer valid
            return HttpResponseRedirect(
                reverse('solr-browse-collection',
                        kwargs={'id': collection.id, 'name': collection.name}))
    else:
        field = fields[0]

    ivalues = FieldValue.objects.filter(
        field=field,
        record__collection__in=collection_and_children,
    ).values('browse_value').distinct().order_by('browse_value')

    if 's' in request.GET:
        start = ivalues.filter(
            browse_value__lt=request.GET['s']).count() // 50 + 1
        return HttpResponseRedirect(reverse(
            'solr-browse-collection',
            kwargs={'id': collection.id, 'name': collection.name}) +
            "?f=%s&page=%s" % (field.id, start))

    try:
        page = int(request.GET['page'])
    except:
        page = 1

    start = (page - 1) * 50
    ivalues_list = [
        row['browse_value']
        for row in ivalues[start:start + 50]
        if row['browse_value'] != ''
    ]

    ivalues_length = ivalues.count()

    values = list(FieldValue.objects.filter(
        field=field,
        record__collection__in=collection_and_children,
        browse_value__in=ivalues_list,
    ).values('value', 'browse_value').annotate(
        freq=Count('record', distinct=True)
    ).order_by('browse_value', 'value'))

    collection_filter = '|'.join(
        str(c.id) for c in collection_and_children
    )

    dummyvalues = DummyContent(ivalues_length)
    paginator = Paginator(dummyvalues, 50)
    page = request.GET.get('page')
    try:
        dummyvalues = paginator.page(page)
    except PageNotAnInteger:
        dummyvalues = paginator.page(1)
    except EmptyPage:
        dummyvalues = paginator.page(paginator.num_pages)

    return render(
        request,
        'browse.html',
        {
            'collections': collections,
            'selected_collection': collection and collection or None,
            'collection_filter': collection_filter,
            'fields': fields,
            'selected_field': field,
            'values': values,
            'ivalues': ivalues,
            'column_split': len(values) // 2,
            'dummyvalues': dummyvalues,
        }
    )


def overview(request):

    collections = filter_by_access(
        request.user, Collection.objects.exclude(hidden=True))
    collections = apply_collection_visibility_preferences(
        request.user, collections)
    collections = collections.annotate(
        num_records=Count('records'))
    children = dict()
    overview_thumbs = dict()
    for coll in collections:
        c = filter_by_access(request.user, coll.children.exclude(hidden=True))
        c = apply_collection_visibility_preferences(
            request.user, c
        )
        children[coll.id] = c

    for record in Record.objects.filter(
        id__in=FieldValue.objects.filter(
            field=get_system_field(),
            value='overview',
            index_value='overview',
        ).values('record'),
    ):
        for coll in record.collection_set.all().values_list('id', flat=True):
            overview_thumbs[coll] = record

    return render(
        request,
        'overview.html',
        {
            'collections': [
                (coll, children[coll.id], overview_thumbs.get(coll.id))
                for coll in collections
            ]
        }
    )


@login_required
def terms(request):

    if not getattr(settings, 'SHOW_TERMS', False):
        raise Http404()

    s = SolrIndex()
    terms = []
    maxfreq = 0

    for term, freq in s.terms().items():
        terms.append([term, freq])
        if freq > maxfreq:
            maxfreq = freq

    for term in terms:
        term[1] = term[1] * 6 // maxfreq

    return render(
        request,
        'terms.html',
        {
            'terms': sorted(terms, key=lambda t: t[0]),
        }
    )


def fieldvalue_autocomplete(request):
    collection_ids = request.GET.get('collections')
    if collection_ids:
        q = Collection.objects.filter(id__in=collection_ids.split(','))
    else:
        q = Collection
    collections = filter_by_access(request.user, q)
    if not collections:
        raise Http404()
    query = request.GET.get('q', '').lower()
    if len(query) >= 2 and len(query) <= 32:
        limit = min(int(request.GET.get('limit', '10')), 100)
        field = request.GET.get('field')
        q = field and Q(field__id=field) or Q()
        values = FieldValue.objects.filter(
            q,
            record__collection__in=collections,
            index_value__istartswith=query).values_list(
            'value', flat=True).distinct()[:limit]
        values = '\n'.join(urlquote(v) for v in values)
    else:
        values = ''
    return HttpResponse(content=values)


def search_form(request):

    collections = filter_by_access(request.user, Collection)
    collections = apply_collection_visibility_preferences(
        request.user, collections)

    def _get_fields():
        return Field.objects.select_related('standard').all().order_by(
            'standard__title', 'name')

    def _cmp(x, y):
        if x == "Other":
            return 1
        if y == "Other":
            return -1
        return (x > y) - (x < y)

    def _field_choices():
        grouped = {}
        for f in _get_fields():
            grouped.setdefault(
                f.standard.title if f.standard else 'Other', []).append(f)
        return [('', 'Any')] + [
            (g, [(f.id, f.label) for f in grouped[g]])
            for g in sorted(grouped, key=cmp_to_key(_cmp))
        ]

    class SearchForm(forms.Form):
        TYPE_CHOICES = (('t', 'in'), ('T', 'not in'))
        criteria = forms.CharField(required=False)
        type = forms.ChoiceField(
            choices=TYPE_CHOICES, required=False, label='')
        field = forms.ChoiceField(
            choices=_field_choices(), required=False, label='')

    def _collection_choices():
        result = []
        for c in collections:
            title = c.title
            children = c.all_child_collections
            if children:
                title += " (including %s sub-collections)" % len(children)
            result.append((c.id, title))
        return result

    class CollectionForm(forms.Form):
        collections = forms.MultipleChoiceField(
            choices=_collection_choices(),
            widget=forms.CheckboxSelectMultiple,
            required=False)

    search_form_formset = formset_factory(form=SearchForm, extra=5)

    if request.method == "POST":
        collectionform = CollectionForm(request.POST, prefix='coll')
        formset = search_form_formset(request.POST, prefix='crit')
        if formset.is_valid() and collectionform.is_valid():
            core_fields = dict(
                (f, f.get_equivalent_fields())
                for f in Field.objects.filter(standard__prefix='dc'))
            query = []
            keywords = []
            for form in formset.forms:
                field = form.cleaned_data['field']
                type = form.cleaned_data['type']
                criteria = form.cleaned_data['criteria']
                if criteria:
                    if field:
                        field = Field.objects.get(id=field)
                        for cf, cfe in core_fields.items():
                            if field == cf or field in cfe:
                                field = cf
                                break
                        query.append('c=%s%s_%s:"%s"' % (
                            type.isupper() and '-' or '',
                            field.name,
                            type.lower(),
                            urlquote(criteria)))
                    else:
                        keywords.append('%s"%s"' % (
                            type.isupper() and '-' or '',
                            urlquote(criteria)))
            collections = collectionform.cleaned_data['collections']
            if collections:
                query.append('c=allcollections:%s' % '|'.join(collections))
            if query or keywords:
                qs = 'kw=%s&' % '+'.join(keywords) + '&'.join(query)
                return HttpResponseRedirect(reverse('solr-search') + '?' + qs)
    else:
        collectionform = CollectionForm(prefix='coll')
        formset = search_form_formset(prefix='crit')

    return render(
        request,
        'search.html',
          {'collectionform': collectionform,
           'formset': formset,
           'collections': collections,
           }
    )
