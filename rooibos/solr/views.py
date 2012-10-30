from django.db.models import Count
from django.core.cache import cache
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django import forms
from django.forms.formsets import formset_factory
from django.db.models import Q
from django.contrib.auth.models import User
from . import SolrIndex
from pysolr import SolrError
from rooibos.access import filter_by_access
import socket
from rooibos.util import safe_int, json_view, calculate_hash
from rooibos.data.models import Field, Collection, FieldValue, Record
from rooibos.data.functions import apply_collection_visibility_preferences, \
    get_collection_visibility_preferences
from rooibos.storage.models import Storage
from rooibos.ui import update_record_selection, clean_record_selection_vars
from rooibos.federatedsearch.views import sidebar_api_raw
import re
import copy
import random
import logging


class SearchFacet(object):

    def __init__(self, name, label):
        self.name = name
        self.label = label

    def process_criteria(self, criteria, *args, **kwargs):
        return criteria

    def set_result(self, facets):
        # break down dicts into tuples
        if hasattr(facets, 'items'):
            self.facets = facets.items()
        else:
            self.facets = facets

    def clean_result(self, hits):
        # sort facet items and remove the ones that match all hits
        self.facets = filter(lambda f: f[1] < hits, getattr(self, 'facets', None) or [])
        self.facets = sorted(self.facets, key=lambda f: len(f) > 2 and f[2] or f[0])

    def or_available(self):
        return True

    def display_value(self, value):
        return value.replace('|', ' or ')

    def federated_search_query(self, value):
        return value.replace('|', ' ')

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

class OwnerSearchFacet(SearchFacet):

    def display_value(self, value):
        value = '|'.join(User.objects.filter(id__in=value.split('|')).values_list('username', flat=True))
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
        presentations = []
        record = Record.objects.filter(id=criteria)
        if record:
            return '|'.join(map(str, record[0].presentationitem_set.all().distinct().values_list('presentation_id', flat=True)))
        else:
            return '-1'

class StorageSearchFacet(SearchFacet):

    _storage_facet_re = re.compile(r'^s(\d+)-(.+)$')

    def __init__(self, name, label, available_storage):
        super(StorageSearchFacet, self).__init__(name, label)
        self.available_storage = available_storage

    def process_criteria(self, criteria, user, *args, **kwargs):
        criteria = '|'.join('s*-%s' %s for s in criteria.split('|'))
        # TODO: need to handle case when no storage is available
        return user.is_superuser and criteria \
            or '(%s) AND (%s)' % (' '.join('s%s-*' % s for s in self.available_storage), criteria)

    def set_result(self, facets):
        result = {}
        if facets:
            for f in facets.keys():
                m = StorageSearchFacet._storage_facet_re.match(f)
                if m and int(m.group(1)) in self.available_storage:
                    result[m.group(2)] = None  # make facet available, but without frequency count
        super(StorageSearchFacet, self).set_result(result)

    def federated_search_query(self, value):
        return ''

class CollectionSearchFacet(SearchFacet):

    def set_result(self, facets):
        result = []
        if facets:
            for id, title in Collection.objects.filter(id__in=map(int, facets.keys())).values_list('id', 'title'):
                result.append((id, facets[str(id)], title))
        super(CollectionSearchFacet, self).set_result(result)

    def display_value(self, value):
        value = '|'.join(Collection.objects.filter(id__in=value.split('|')).values_list('title', flat=True))
        return super(CollectionSearchFacet, self).display_value(value)

    def federated_search_query(self, value):
        return ''

_special = re.compile(r'(\+|-|&&|\|\||!|\(|\)|\{|}|\[|\]|\^|"|~|\*|\?|:|\\)')


class ExactValueSearchFacet(SearchFacet):

    def __init__(self, name):
        prefix, name = ([None] + name[:-2].split('.'))[-2:]
        if prefix:
            field = Field.objects.get(standard__prefix=prefix, name=name)
        else:
            field = Field.objects.get(standard=None, name=name)
        super(ExactValueSearchFacet, self).__init__(name, field.label)

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


def _generate_query(search_facets, user, collection, criteria, keywords, selected, *exclude):

    # add owned tag facet
    search_facets['ownedtag'] = OwnedTagSearchFacet()

    fields = {}
    for c in criteria:
        if (c in exclude) or (':' not in c):
            continue
        (f, o) = c.split(':', 1)
        if f.startswith('-'):
            f = 'NOT ' + f[1:]
        fname = f.rsplit(' ',1)[-1]

        # create exact match criteria on the fly if needed
        if fname.endswith('_s') and not search_facets.has_key(fname):
            search_facets[fname] = ExactValueSearchFacet(fname)

        if search_facets.has_key(fname):
            o = search_facets[fname].process_criteria(o, user)
            fields.setdefault(f, []).append('(' + o.replace('|', ' OR ') + ')')

    fields = map(lambda (name, crit): '%s:(%s)' % (name, (name.startswith('NOT ') and ' OR ' or ' AND ').join(crit)),
                 fields.iteritems())

    def build_keywords(q, k):
        k = k.lower()
        if k == 'and' or k == 'or':
            return q + ' ' + k.upper()
        elif q.endswith(' AND') or q.endswith(' OR'):
            return q + ' ' + k
        else:
            return q + ' AND ' + k

    if keywords: keywords = reduce(build_keywords, keywords.split())

    query = ''
    if fields:
        query = ' AND '.join(fields)
    if keywords:
        query = query and '%s AND (%s)' % (query, keywords) or '(%s)' % keywords
    if not query:
        query = '*:*'
    if collection:
        query = 'collections:%s AND %s' % (collection.id, query)
    if hasattr(selected, '__len__'):
        query = 'id:(%s) AND %s' % (' '.join(map(str, selected or [-1])), query)

    if not user.is_superuser:
        collections = ' '.join(map(str, filter_by_access(user, Collection).values_list('id', flat=True)))
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
            c.append('acl_read:((%su%d) AND NOT U%d)' % (groups, user.id, user.id))
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

    available_storage = list(filter_by_access(user, Storage).values_list('id', flat=True))
    exclude_facets = ['identifier']
    fields = Field.objects.filter(standard__prefix='dc').exclude(name__in=exclude_facets)

    search_facets = [SearchFacet('tag', 'Tags')] + [SearchFacet(field.name + '_t', field.label) for field in fields]
    search_facets.append(StorageSearchFacet('resolution', 'Image size', available_storage))
    search_facets.append(StorageSearchFacet('mimetype', 'Media type', available_storage))
    search_facets.append(CollectionSearchFacet('allcollections', 'Collection'))
    search_facets.append(OwnerSearchFacet('owner', 'Owner'))
    search_facets.append(RelatedToSearchFacet('presentations', 'Related to'))
    search_facets.append(RecordDateSearchFacet('modified', 'Last modified'))
    search_facets.append(RecordDateSearchFacet('created', 'Record created'))
    # convert to dictionary
    search_facets = dict((f.name, f) for f in search_facets)

    query = _generate_query(search_facets, user, collection, criteria, keywords, selected, remove)

    s = SolrIndex()

    return_facets = search_facets.keys() if produce_facets else []

    try:
        (hits, records, facets) = s.search(query, sort=sort, rows=pagesize, start=(page - 1) * pagesize,
                                           facets=return_facets, facet_mincount=1, facet_limit=100)
    except SolrError:
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
        (f, v) = orquery.split(':', 1)
        orfacets = s.search(_generate_query(search_facets, user, collection, criteria, keywords, selected,
                                            remove, orquery),
                            rows=0, facets=[f], facet_mincount=1, facet_limit=100)[2]
        orfacet = copy.copy(search_facets[f])
        orfacet.label = '%s in %s or...' % (v.replace("|", " or "), orfacet.label)
        orfacet.set_result(orfacets[f])
    else:
        orfacet = None

    return (hits, records, search_facets, orfacet, query, fields)



def search(request, id=None, name=None, selected=False, json=False):
    collection = id and get_object_or_404(filter_by_access(request.user, Collection), id=id) or None

    if request.method == "POST":
        update_record_selection(request)
        # redirect to get request with updated parameters
        q = request.GET.copy()
        q.update(request.POST)
        q = clean_record_selection_vars(q)
        for i, v in q.items():
            if i != 'c':
                q[i] = v  # replace multiple values with last one except for criteria ('c')
        q.pop('v.x', None)
        q.pop('v.y', None)
        q.pop('x', None)
        q.pop('y', None)
        return HttpResponseRedirect(request.path + '?' + q.urlencode())

    # get parameters relevant for search
    criteria = request.GET.getlist('c')
    remove = request.GET.get('rem', None)
    if remove and remove in criteria: criteria.remove(remove)
    keywords = request.GET.get('kw', '')

    # get parameters relevant for view

    viewmode = request.GET.get('v', 'thumb')
    if viewmode == 'list':
        pagesize = max(min(safe_int(request.GET.get('ps', '50'), 50), 100), 5)
    else:
        pagesize = max(min(safe_int(request.GET.get('ps', '30'), 30), 50), 5)
    page = safe_int(request.GET.get('page', '1'), 1)
    sort = request.GET.get('s', 'title_sort').lower()
    if not sort.endswith(" asc") and not sort.endswith(" desc"): sort += " asc"

    orquery = request.GET.get('or', None)
    user = request.user

    if request.GET.has_key('action'):
        page = safe_int(request.GET.get('op', '1'), 1)

    if selected:
        selected = request.session.get('selected_records', ())

    (hits, records, search_facets, orfacet, query, fields) = run_search(user, collection, criteria, keywords, sort, page, pagesize,
                                                         orquery, selected, remove, produce_facets=False)

    if json:
        return (hits, records, viewmode)

    if collection:
        url = reverse('solr-search-collection', kwargs={'id': collection.id, 'name': collection.name})
        furl = reverse('solr-search-collection-facets', kwargs={'id': collection.id, 'name': collection.name})
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
    #for f in q:
    #    if f != 'kw':
    #        for l in q.getlist(f):
    #            hiddenfields.append((f, l))
    qurl = q.urlencode()
    q.setlist('c', filter(lambda c: c != orquery, criteria))
    qurl_orquery = q.urlencode()
    limit_url = "%s?%s%s" % (url, qurl, qurl and '&' or '')
    limit_url_orquery = "%s?%s%s" % (url, qurl_orquery, qurl_orquery and '&' or '')
    facets_url = "%s?%s%s" % (furl, qurl, qurl and '&' or '')

    form_url = "%s?%s" % (url, q.urlencode())

    prev_page_url = None
    next_page_url = None

    if page > 1:
        q['page'] = page - 1
        prev_page_url = "%s?%s" % (url, q.urlencode())
    if page < (hits - 1) / pagesize + 1:
        q['page'] = page + 1
        next_page_url = "%s?%s" % (url, q.urlencode())


    def readable_criteria(c):
        (f, o) = c.split(':', 1)
        negated = f.startswith('-')
        f = f[1 if negated else 0:]
        if search_facets.has_key(f):
            return dict(facet=c,
                        term=search_facets[f].display_value(o),
                        label=search_facets[f].label,
                        negated=negated,
                        or_available=not negated and search_facets[f].or_available())
        else:
            return dict(facet=c,
                        term=o,
                        label='Unknown criteria',
                        negated=negated,
                        or_available=False)

    def reduce_federated_search_query(q, c):
        (f, o) = c.split(':', 1)
        if f.startswith('-') or not search_facets.has_key(f):
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
    print hash
    facets = cache.get('search_facets_html_%s' % hash)

    sort = sort.startswith('random') and 'random' or sort.split()[0]
    sort = sort.endswith('_sort') and sort[:-5] or sort

    federated_search_query = reduce(reduce_federated_search_query, criteria, keywords)
    federated_search = sidebar_api_raw(
        request, federated_search_query, cached_only=True) if federated_search_query else None

    return render_to_response('results.html',
                          {'criteria': map(readable_criteria, criteria),
                           'query': query,
                           'keywords': keywords,
                           'hiddenfields': hiddenfields,
                           'records': records,
                           'hits': hits,
                           'page': page,
                           'pages': (hits - 1) / pagesize + 1,
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
                           'federated_search': federated_search,
                           'federated_search_query': federated_search_query,
                           'pagination_helper': [None] * hits,
                           'has_record_created_criteria': any(f.startswith('created:') for f in criteria),
                           'has_last_modified_criteria': any(f.startswith('modified:') for f in criteria),
                           },
                          context_instance=RequestContext(request))


@json_view
def search_facets(request, id=None, name=None, selected=False):

    collection = id and get_object_or_404(filter_by_access(request.user, Collection), id=id) or None

    # get parameters relevant for search
    criteria = request.GET.getlist('c')
    remove = request.GET.get('rem', None)
    if remove and remove in criteria: criteria.remove(remove)
    keywords = request.GET.get('kw', '')

    user = request.user

    if selected:
        selected = request.session.get('selected_records', ())

    (hits, records, search_facets, orfacet, query, fields) = run_search(user, collection, criteria, keywords,
                                                         selected=selected, remove=remove, produce_facets=True)

    if collection:
        url = reverse('solr-search-collection', kwargs={'id': collection.id, 'name': collection.name})
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

    # sort facets by label
    facets = sorted(search_facets.values(), key=lambda f: f.label)

    # clean facet items
    for f in facets:
        f.clean_result(hits)

    # remove facets with only no filter options
    facets = filter(lambda f: len(f.facets) > 0, facets)

    html = render_to_string('results_facets.html',
                          {
                           'limit_url': limit_url,
                           'facets': facets
                           },
                          context_instance=RequestContext(request))

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

    html = render_to_string('results_bare_' + templates.get(viewmode, 'icons') + '.html',
                              {'records': records,
                               'selectable': True,},
                              context_instance=RequestContext(request))

    return dict(html=html)


def browse(request, id=None, name=None):
    collections = filter_by_access(request.user, Collection)
    collections = apply_collection_visibility_preferences(request.user, collections)
    collections = collections.annotate(num_records=Count('records')).filter(num_records__gt=0).order_by('title')

    if not collections:
        return render_to_response('browse.html',
                              {},
                              context_instance=RequestContext(request))

    if request.GET.has_key('c'):
        collection = get_object_or_404(collections, name=request.GET['c'])
        return HttpResponseRedirect(reverse('solr-browse-collection',
                                            kwargs={'id': collection.id, 'name': collection.name}))

    collection = id and get_object_or_404(collections, id=id) or collections[0]

    fields = cache.get('browse_fields_%s' % collection.id)
    if fields:
        fields = list(Field.objects.filter(id__in=fields))
    else:
        fields = list(Field.objects.filter(fieldvalue__record__collection=collection).distinct())
        cache.set('browse_fields_%s' % collection.id, [f.id for f in fields], 60)

    if not fields:
        raise Http404()

    if request.GET.has_key('f'):
        try:
            field = get_object_or_404(Field, id=request.GET['f'], id__in=(f.id for f in fields))
        except ValueError:
            # GET['f'] was text previously and external links exist that are no longer valid
            return HttpResponseRedirect(reverse('solr-browse-collection',
                                        kwargs={'id': collection.id, 'name': collection.name}))
    else:
        field = fields[0]

    values = FieldValue.objects.filter(field=field, record__collection=collection).values('value').annotate(freq=Count('value', distinct=False)).order_by('value')

    if request.GET.has_key('s'):
        start = values.filter(value__lt=request.GET['s']).count() / 50 + 1
        return HttpResponseRedirect(reverse('solr-browse-collection',
                                            kwargs={'id': collection.id, 'name': collection.name}) +
                                    "?f=%s&page=%s" % (field.id, start))

    return render_to_response('browse.html',
                              {'collections': collections,
                               'selected_collection': collection and collection or None,
                               'fields': fields,
                               'selected_field': field,
                               'values': values,},
                              context_instance=RequestContext(request))


def overview(request):

    collections = filter_by_access(request.user, Collection)
    collections = apply_collection_visibility_preferences(request.user, collections)
    collections = collections.order_by('title').annotate(num_records=Count('records'))

    return render_to_response('overview.html',
                              {'collections': collections,},
                              context_instance=RequestContext(request))


def fieldvalue_autocomplete(request):
    collection_ids = request.GET.get('collections')
    q = collection_ids and Collection.objects.filter(id__in=collection_ids.split(',')) or Collection
    collections = filter_by_access(request.user, q)
    if not collections:
        raise Http404()
    query = request.GET.get('q', '').lower()
    if len(query) >= 2 and len(query) <= 32:
        limit = min(int(request.GET.get('limit', '10')), 100)
        field = request.GET.get('field')
        q = field and Q(field__id=field) or Q()
        values = FieldValue.objects.filter(q, record__collection__in=collections, index_value__istartswith=query) \
            .values_list('value', flat=True).distinct()[:limit] #.order_by('value')
        #print values.query.as_sql()
        values = '\n'.join(urlquote(v) for v in values)
    else:
        values = ''
    return HttpResponse(content=values)


def search_form(request):

    collections = filter_by_access(request.user, Collection)
    collections = apply_collection_visibility_preferences(request.user, collections)
    if not collections:
        raise Http404()

    def _get_fields():
        return Field.objects.select_related('standard').all().order_by('standard__title', 'name')

    def _cmp(x, y):
        if x == "Other": return 1
        if y == "Other": return -1
        return cmp(x, y)

    def _field_choices():
        grouped = {}
        for f in _get_fields():
            grouped.setdefault(f.standard and f.standard.title or 'Other', []).append(f)
        return [('', 'Any')] + [(g, [(f.id, f.label) for f in grouped[g]]) for g in sorted(grouped, _cmp)]

    class SearchForm(forms.Form):
        TYPE_CHOICES = (('t', 'in'), ('T', 'not in'))
        criteria = forms.CharField(required=False)
        type = forms.ChoiceField(choices=TYPE_CHOICES, required=False, label='')
        field = forms.ChoiceField(choices=_field_choices(), required=False, label='')

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
        collections = forms.MultipleChoiceField(choices=_collection_choices(),
                                                widget=forms.CheckboxSelectMultiple,
                                                required=False)

    SearchFormFormSet = formset_factory(form=SearchForm, extra=5)

    if request.method == "POST":
        collectionform = CollectionForm(request.POST, prefix='coll')
        formset = SearchFormFormSet(request.POST, prefix='crit')
        if formset.is_valid() and collectionform.is_valid():
            core_fields = dict((f, f.get_equivalent_fields()) for f in Field.objects.filter(standard__prefix='dc'))
            query = []
            keywords = []
            for form in formset.forms:
                field = form.cleaned_data['field']
                type = form.cleaned_data['type']
                criteria = form.cleaned_data['criteria']
                if criteria:
                    if field:
                        field = Field.objects.get(id=field)
                        for cf, cfe in core_fields.iteritems():
                            if field == cf or field in cfe:
                                field = cf
                                break
                        query.append('c=%s%s_%s:"%s"' % (type.isupper() and '-' or '', field.name, type.lower(), urlquote(criteria)))
                    else:
                        keywords.append('%s"%s"' % (type.isupper() and '-' or '', urlquote(criteria)))
            collections = collectionform.cleaned_data['collections']
            if collections:
                query.append('c=allcollections:%s' % '|'.join(collections))
            if query or keywords:
                qs = 'kw=%s&' % '+'.join(keywords) + '&'.join(query)
                return HttpResponseRedirect(reverse('solr-search') + '?' + qs)
    else:
        collectionform = CollectionForm(prefix='coll')
        formset = SearchFormFormSet(prefix='crit')

    return render_to_response('search.html',
                              {'collectionform': collectionform,
                               'formset': formset,
                               },
                              context_instance=RequestContext(request))
