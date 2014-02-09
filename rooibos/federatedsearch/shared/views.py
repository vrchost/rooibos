from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.http import urlencode
from django.http import HttpResponse, Http404
import urllib2
import math
import urllib
import cookielib
from django.utils import simplejson
from rooibos.data.models import Collection, CollectionItem, Record, \
    Field, FieldValue, standardfield
from rooibos.storage import Storage
from rooibos.access.models import AccessControl, ExtendedGroup, \
    AUTHENTICATED_GROUP
from rooibos.workers.models import JobInfo
from django.conf import settings
from django.core.urlresolvers import reverse
from rooibos.federatedsearch.models import FederatedSearch, HitCount
import datetime
import socket
import json
import logging
import os


class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result


def _fetch_url(url, username, password, timeout=10):
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(
        cookielib.CookieJar()), SmartRedirectHandler())
    request = urllib2.Request(url)

    import base64
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    request.add_header("Authorization", "Basic %s" % base64string)

    socket.setdefaulttimeout(timeout)
    response = opener.open(request)
    return response


def _getShared(name):
    shared_collections = getattr(settings, 'SHARED_COLLECTIONS', {})
    return shared_collections.get(name)


class SharedSearch(FederatedSearch):

    def _load(self, shared, keyword, page=1, pagesize=30):
        url = "%s%s?%s" % (
            shared['server'],
            shared['url'],
            urllib.urlencode([
                ('kw', keyword), ('page', page), ('ps', pagesize)
            ])
        )
        try:
            response = _fetch_url(url, shared['username'], shared['password'],
                                  self.timeout)
            data = json.loads(response.read())
            return data
        except Exception:
            logging.exception('Shared collection search failed')
        return {}

    def hits_count(self, keyword):
        shared = _getShared('Test')
        if not shared:
            return 0
        data = self._load(shared, keyword)
        if data.get('result') == 'ok':
            return data.get('hits', 0)
        else:
            return 0

    def get_label(self):
        return "Shared"

    def get_search_url(self):
        return reverse('shared-search')

    def get_source_id(self):
        return "shared"

    def search(self, keyword, page=1, pagesize=30):
        cached, created = HitCount.current_objects.get_or_create(
            source=self.get_source_id(),
            query='%s [%s:%s]' % (keyword, page, pagesize),
            defaults=dict(
                hits=0,
                valid_until=datetime.datetime.now() + datetime.timedelta(1)
                )
            )
        if not created and cached.results:
            return simplejson.loads(cached.results)

        shared = _getShared('Test')
        data = self._load(shared, keyword, page, pagesize)

        total = data.get('hits', 0)
        if not total:
            return None

        # make URLs absolute if they are relative
        for record in data.get('records'):
            if 'thumbnail' in record and '://' not in record['thumbnail']:
                record['thumbnail'] = '%s?%s' % (
                    reverse('shared-proxy-image'),
                    urllib.urlencode([('url', record['thumbnail'])])
                    )
            if 'image' in record and '://' not in record['image']:
                record['image'] = '%s?%s' % (
                    reverse('shared-proxy-image'),
                    urllib.urlencode([('url', record['image'])])
                    )

        cached.results = simplejson.dumps(data, separators=(',', ':'))
        cached.save()
        return data

    @classmethod
    def available(cls):
        return bool(getattr(settings, 'SHARED_COLLECTIONS', None))

    def get_collection(self):
        collection, created = Collection.objects.get_or_create(
            name=self.get_source_id(),
            defaults=dict(
                title=self.get_label(),
                hidden=True,
                description='Local copies of shared collection images',
                )
            )
        if created:
            authenticated_users, created = ExtendedGroup.objects.get_or_create(
                type=AUTHENTICATED_GROUP)
            AccessControl.objects.create(content_object=collection,
                                         usergroup=authenticated_users,
                                         read=True)
        return collection

    def get_storage(self):
        storage, created = Storage.objects.get_or_create(
            name=self.get_source_id(),
            defaults=dict(
                title=self.get_label(),
                system='local',
                base=os.path.join(settings.AUTO_STORAGE_DIR,
                                  self.get_source_id())
                )
            )
        if created:
            authenticated_users, created = ExtendedGroup.objects.get_or_create(
                type=AUTHENTICATED_GROUP)
            AccessControl.objects.create(content_object=storage,
                                         usergroup=authenticated_users,
                                         read=True)
        return storage

    def create_record(self, remote_id):
        shared = _getShared('Test')
        collection = self.get_collection()

        url = shared['server'] + reverse('api-record', kwargs={
            'id': remote_id, 'name': '_'})

        response = _fetch_url(url, shared['username'], shared['password'])
        data = json.loads(response.read())

        title = data['record']['title']
        image_url = data['record']['image']
        if not '://' in image_url:
            image_url = shared['server'] + image_url

        record = Record.objects.create(name=title,
                                       source=url,
                                       manager='shared')

        unmapped_field, created = Field.objects.get_or_create(
            name='shared-data',
            defaults={
                'label': 'Metadata',
            }
        )

        for index, metadata in enumerate(data['record']['metadata']):
            try:
                field = standardfield(metadata['dc']) if metadata.get('dc') else unmapped_field
            except Field.DoesNotExist:
                field = unmapped_field
            FieldValue.objects.create(record=record,
                                      field=field,
                                      order=metadata.get('order', index),
                                      value=metadata['value'],
                                      label=metadata['label'],
                                     )

        CollectionItem.objects.create(collection=collection, record=record)

        # create job to download actual media file
        job = JobInfo.objects.create(
            func='shared_download_media',
            arg=simplejson.dumps(dict(record=record.id, url=image_url)))
        job.run()

        return record


@login_required
def search(request):

    pagesize = 50

    query = request.GET.get('q', '') or request.POST.get('q', '')
    try:
        page = int(request.GET.get('p', 1))
    except ValueError:
        page = 1

    a = SharedSearch()

    try:
        results = a.search(query, page, pagesize) if query else None
        failure = False
    except urllib2.HTTPError:
        results = None
        failure = True

    pages = int(math.ceil(float(results['hits']) / pagesize)) if results else 0
    prev_page_url = ("?" + urlencode((('q', query), ('p', page - 1)))
                     if page > 1 else None)
    next_page_url = ("?" + urlencode((('q', query), ('p', page + 1)))
                     if page < pages else None)

    return render_to_response('federatedsearch/shared/results.html', {
        'query': query,
        'results': results,
        'page': page,
        'failure': failure,
        'pages': pages,
        'prev_page': prev_page_url,
        'next_page': next_page_url,
        },
        context_instance=RequestContext(request))


@login_required
def proxy_image(request):

    shared = _getShared('Test')
    url = shared['server'] + request.GET.get('url')

    response = _fetch_url(url, shared['username'], shared['password'])
    return HttpResponse(content=response.read(),
                        content_type=response.info().gettype())


def select(request):
    if not request.user.is_authenticated():
        raise Http404()

    if request.method == "POST":
        search = SharedSearch()
        remote_ids = simplejson.loads(request.POST.get('id', '[]'))

        # find records that already have been created for the given URLs
        ids = dict(Record.objects.filter(
            source__in=remote_ids,
            manager='shared').values_list('source', 'id'))
        result = []
        for remote_id in remote_ids:
            id = ids.get(remote_id)
            if id:
                result.append(id)
            else:
                record = search.create_record(remote_id)
                result.append(record.id)
        # rewrite request and submit to regular selection code
        r = request.POST.copy()
        r['id'] = simplejson.dumps(result)
        request.POST = r

    from rooibos.ui.views import select_record
    return select_record(request)
