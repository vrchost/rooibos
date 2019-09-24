from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils.http import urlencode
from django.http import HttpResponse, Http404, HttpResponseRedirect
import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse
import math
import urllib.request, urllib.parse, urllib.error
import http.cookiejar
import json as simplejson
from rooibos.data.models import Collection, CollectionItem, Record, \
    Field, FieldValue, standardfield
from django.conf import settings
from django.core.urlresolvers import reverse
from django import forms
from rooibos.federatedsearch import FederatedSearch
from rooibos.access.functions import filter_by_access, sync_access
from .models import SharedCollection
import datetime
import socket
import json
import logging
import os


class SmartRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib.request.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib.request.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result


def _fetch_url(url, username, password, timeout=10):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(
        http.cookiejar.CookieJar()), SmartRedirectHandler())
    request = urllib.request.Request(url)

    if username and password:
        import base64
        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
        request.add_header("Authorization", "Basic %s" % base64string)

    socket.setdefaulttimeout(timeout)
    response = opener.open(request)
    return response


class SharedSearch(FederatedSearch):

    @classmethod
    def available(cls):
        return bool(getattr(settings, 'SHARED_COLLECTIONS', None))

    @classmethod
    def get_instances(cls, user):
        for shared in filter_by_access(user, SharedCollection.objects.all()):
            yield SharedSearch(shared)

    def __init__(self, shared, *args, **kwargs):
        super(SharedSearch, self).__init__(*args, **kwargs)
        if not isinstance(shared, SharedCollection):
            shared = SharedCollection.objects.get(id=shared)
        self.shared = shared

    def _load(self, keyword, page=1, pagesize=30):
        url = "%s?%s" % (
            self.shared.url,
            urllib.parse.urlencode([
                ('kw', keyword), ('page', page), ('ps', pagesize)
            ])
        )
        try:
            response = _fetch_url(
                url, self.shared.username, self.shared.password, self.timeout)
            data = json.loads(response.read())
            return data
        except Exception:
            logging.exception('Shared collection search failed')
        return {}

    def hits_count(self, keyword):
        data = self._load(keyword)
        if data.get('result') == 'ok':
            return data.get('hits', 0)
        else:
            return 0

    def get_label(self):
        return self.shared.title

    def get_search_url(self):
        return reverse('shared-search',
                       kwargs={'id': self.shared.id, 'name': self.shared.name})

    def get_source_id(self):
        return 'shared_%s' % self.shared.name

    def search(self, keyword, page=1, pagesize=30):

        from rooibos.federatedsearch.models import HitCount

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

        data = self._load(keyword, page, pagesize)

        total = data.get('hits', 0)
        if not total:
            return None

        # make URLs absolute if they are relative
        for record in data.get('records'):
            if 'thumbnail' in record and '://' not in record['thumbnail']:
                record['thumbnail'] = '%s?%s' % (
                    reverse('shared-proxy-image',
                            kwargs={'id': self.shared.id,
                                    'name': self.shared.name}),
                    urllib.parse.urlencode([('url', record['thumbnail'])])
                )
            if 'image' in record and '://' not in record['image']:
                record['image'] = '%s?%s' % (
                    reverse('shared-proxy-image',
                            kwargs={'id': self.shared.id,
                                    'name': self.shared.name}),
                    urllib.parse.urlencode([('url', record['image'])])
                )

        cached.results = simplejson.dumps(data, separators=(',', ':'))
        cached.save()
        return data

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
            sync_access(self.shared, collection)
        return collection

    def get_storage(self):

        from rooibos.storage.models import Storage

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
            sync_access(self.shared, storage)
        return storage

    def create_record(self, remote_id):
        collection = self.get_collection()

        url = urlparse(self.shared.url)
        server = '://'.join([url.scheme, url.netloc])

        url = server + reverse('api-record', kwargs={
            'id': remote_id, 'name': '_'})

        response = _fetch_url(url, self.shared.username, self.shared.password)
        data = json.loads(response.read())

        title = data['record']['title']
        image_url = data['record']['image']
        if '://' not in image_url:
            image_url = server + image_url

        record = Record.objects.create(name=title,
                                       source=url,
                                       manager=self.get_source_id())

        unmapped_field, created = Field.objects.get_or_create(
            name='shared-data',
            defaults={
                'label': 'Metadata',
            }
        )

        for index, metadata in enumerate(data['record']['metadata']):
            try:
                field = (standardfield(metadata['dc'])
                         if metadata.get('dc') else unmapped_field)
            except Field.DoesNotExist:
                field = unmapped_field
            FieldValue.objects.create(
                record=record,
                field=field,
                order=metadata.get('order', index),
                value=metadata['value'],
                label=metadata['label'],
            )

        CollectionItem.objects.create(collection=collection, record=record)

        # create job to download actual media file
        from .tasks import shared_download_media
        shared_download_media.delay(self.shared.id, record.id, image_url)

        return record


@login_required
def search(request, id, name):

    pagesize = 50

    query = request.GET.get('q', '') or request.POST.get('q', '')
    try:
        page = int(request.GET.get('p', 1))
    except ValueError:
        page = 1

    shared = SharedSearch(id)

    try:
        results = shared.search(query, page, pagesize) if query else None
        failure = False
    except urllib.error.HTTPError:
        results = None
        failure = True

    pages = int(math.ceil(float(results['hits']) / pagesize)) if results else 0
    prev_page_url = ("?" + urlencode((('q', query), ('p', page - 1)))
                     if page > 1 else None)
    next_page_url = ("?" + urlencode((('q', query), ('p', page + 1)))
                     if page < pages else None)

    return render(request,
        'federatedsearch/shared/results.html', {
            'shared': shared.shared,
            'query': query,
            'results': results,
            'page': page,
            'failure': failure,
            'pages': pages,
            'prev_page': prev_page_url,
            'next_page': next_page_url,
        }
    )


@login_required
def proxy_image(request, id, name):

    shared = SharedSearch(id).shared

    url = urlparse(shared.url)
    server = '://'.join([url.scheme, url.netloc])

    url = server + request.GET.get('url')

    response = _fetch_url(url, shared.username, shared.password)
    return HttpResponse(content=response.read(),
                        content_type=response.info().gettype())


def select(request, id, name):
    if not request.user.is_authenticated():
        raise Http404()

    if request.method == "POST":
        shared = SharedSearch(id)
        remote_ids = simplejson.loads(request.POST.get('id', '[]'))

        # find records that already have been created for the given URLs
        ids = dict(Record.objects.filter(
            source__in=remote_ids,
            manager=shared.get_source_id()).values_list('source', 'id'))
        result = []
        for remote_id in remote_ids:
            id = ids.get(remote_id)
            if id:
                result.append(id)
            else:
                record = shared.create_record(remote_id)
                result.append(record.id)
        # rewrite request and submit to regular selection code
        r = request.POST.copy()
        r['id'] = simplejson.dumps(result)
        request.POST = r

    from rooibos.ui.views import select_record
    return select_record(request)


@login_required
def manage(request):
    if not request.user.is_superuser:
        raise Http404()

    return render(request,
        'federatedsearch/shared/manage.html',
        {
            'collections': SharedCollection.objects.all(),
        }
    )


@login_required
def edit(request, id=None, name=None):
    if not request.user.is_superuser:
        raise Http404()

    if id and name:
        collection = get_object_or_404(SharedCollection, id=id)
    else:
        collection = SharedCollection(title='Untitled')

    class SharedCollectionForm(forms.ModelForm):

        url = forms.CharField()
        username = forms.CharField()
        password = forms.CharField()

        class Meta:
            model = SharedCollection
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super(SharedCollectionForm, self).__init__(*args, **kwargs)
            self.fields['url'].initial = self.instance.url
            self.fields['username'].initial = self.instance.username
            self.fields['password'].initial = self.instance.password

        def save(self, commit=True):
            self.instance.url = self.cleaned_data['url']
            self.instance.username = self.cleaned_data['username']
            self.instance.password = self.cleaned_data['password']
            super(SharedCollectionForm, self).save(commit=commit)

    if request.method == "POST":
        if request.POST.get('delete-collection'):
            messages.add_message(
                request,
                messages.INFO,
                message="Shared collection '%s' has been removed." %
                        collection.title
            )
            collection.delete()
            return HttpResponseRedirect(reverse('shared-manage'))
        else:
            form = SharedCollectionForm(request.POST, instance=collection)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('shared-edit', kwargs=dict(
                    id=form.instance.id, name=form.instance.name)))
    else:
        form = SharedCollectionForm(instance=collection)

    return render(request,
        'federatedsearch/shared/edit.html',
        {
            'form': form,
            'collection': collection,
        }
    )
