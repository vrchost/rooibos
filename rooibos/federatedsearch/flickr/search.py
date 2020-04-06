from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.cache import cache
from rooibos.access.models import AccessControl, ExtendedGroup, \
    AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, \
    CollectionItem, FieldValue
from rooibos.federatedsearch import FederatedSearch
import flickrapi
import urllib.request, urllib.error, urllib.parse
import os


class FlickrSearch(FederatedSearch):

    def __init__(self):
        self.flickr = flickrapi.FlickrAPI(
            settings.FLICKR_KEY,
            settings.FLICKR_SECRET,
            cache=True,
            store_token=False
        )

    def hits_count(self, keyword):
        cc_licenses = ','.join(self.get_cc_licenses())
        results = self.flickr.flickr_call(
            method='flickr.photos.search',
            text=keyword,
            api_key=settings.FLICKR_KEY,
            format='xmlnode',
            page=1,
            per_page=1,
            license=cc_licenses,
        )
        return int(results.photos[0]['total'])

    def get_label(self):
        return "Flickr"

    def get_search_url(self):
        return reverse('flickr-search')

    def get_source_id(self):
        return "Flickr"

    def get_collection(self):
        collection, created = Collection.objects.get_or_create(
            name='flickr',
            defaults=dict(
                title='Flickr',
                hidden=True,
                description='Flickr Collection'
            )
        )
        if created:
            authenticated_users, created = ExtendedGroup.objects.get_or_create(
                type=AUTHENTICATED_GROUP)
            AccessControl.objects.create(
                content_object=collection,
                usergroup=authenticated_users,
                read=True
            )
        return collection

    def get_storage(self):

        from rooibos.storage.models import Storage

        storage, created = Storage.objects.get_or_create(
            name='flickr',
            defaults=dict(
                title='Flickr',
                system='local',
                base=os.path.join(settings.AUTO_STORAGE_DIR, 'flickr')
            )
        )
        if created:
            authenticated_users, created = ExtendedGroup.objects.get_or_create(
                type=AUTHENTICATED_GROUP)
            AccessControl.objects.create(
                content_object=storage,
                usergroup=authenticated_users,
                read=True
            )
        return storage

    def get_licenses(self):
        if not hasattr(self, '_licenses'):
            self._licenses = cache.get('flickr.photos.licenses.getInfo')
            if not self._licenses:
                results = self.flickr.flickr_call(
                    method='flickr.photos.licenses.getInfo',
                    api_key=settings.FLICKR_KEY,
                    format='xmlnode',
                )
                self._licenses = dict(
                    (l['id'], dict(name=l['name'], url=l['url']))
                    for l in results.licenses[0].license
                )
                cache.set(
                    'flickr.photos.licenses.getInfo', self._licenses, 3600)
        return self._licenses

    def get_license(self, id):
        return self.get_licenses().get(id)

    def get_cc_licenses(self):
        return [id for id, license in self.get_licenses().items()
                if license['url'].startswith('http://creativecommons.org/')]

    def search(self, query, page=1, pagesize=50, sort='date-posted-desc'):
        if not query:
            return None
        cc_licenses = ','.join(self.get_cc_licenses())
        try:
            results = self.flickr.flickr_call(
                method='flickr.photos.search',
                text=query,
                api_key=settings.FLICKR_KEY,
                format='xmlnode',
                page=page,
                per_page=pagesize,
                extras='url_t,license,owner_name',
                license=cc_licenses,
                sort=sort
            )

            images = [
                dict(
                    flickr_id=image['id'],
                    title=image['title'] or 'Untitled',
                    thumb_url=image['url_t'],
                    record_url="http://www.flickr.com/photos/%s/%s" % (
                        image['owner'], image['id']),
                    license=self.get_license(image['license']),
                    owner=image['ownername'],
                )
                for image in results.photos[0].photo
            ] if hasattr(results.photos[0], 'photo') else []

            hits = int(results.photos[0]['total'])
        except (urllib.error.HTTPError, urllib.error.URLError, flickrapi.FlickrError):
            images = []
            hits = 0

        return dict(records=images, hits=hits)

    def create_record(self, remote_id):
        collection = self.get_collection()

        results = self.flickr.flickr_call(method='flickr.photos.getInfo',
                                          api_key=settings.FLICKR_KEY,
                                          photo_id=remote_id,
                                          format='xmlnode')

        def get_property(exp):
            try:
                return exp(results.photo[0])
            except (KeyError, AttributeError):
                return None

        username = get_property(lambda r: r.owner[0]['username'])
        realname = get_property(lambda r: r.owner[0]['realname'])

        title = get_property(lambda r: r.title[0].text) or 'Untitled'
        description = get_property(lambda r: r.description[0].text)
        date = get_property(lambda r: r.dates[0]['taken'])
        url = get_property(lambda r: r.urls[0].url[0].text)

        tags = get_property(lambda r: r.tags[0].tag)
        tags = [tag.text for tag in tags] if tags else []

        info = self.flickr.flickr_call(method='flickr.photos.getSizes',
                                       api_key=settings.FLICKR_KEY,
                                       photo_id=remote_id,
                                       format='xmlnode')

        image_url = info.sizes[0].size[-1]['source']

        record = Record.objects.create(name=title,
                                       source=url,
                                       manager='flickr')

        FieldValue.objects.create(record=record,
                                  field=standardfield('title'),
                                  order=0,
                                  value=title)
        if description:
            FieldValue.objects.create(record=record,
                                      field=standardfield('description'),
                                      order=1,
                                      value=description)
        if date:
            FieldValue.objects.create(record=record,
                                      field=standardfield('date'),
                                      order=2,
                                      value=date)
        FieldValue.objects.create(record=record,
                                  field=standardfield('identifier'),
                                  order=3,
                                  value=remote_id)
        if username:
            FieldValue.objects.create(record=record,
                                      field=standardfield('contributor'),
                                      order=4,
                                      value=username)
        if realname:
            FieldValue.objects.create(record=record,
                                      field=standardfield('contributor'),
                                      order=5,
                                      value=realname)
        for tag in tags:
            FieldValue.objects.create(record=record,
                                      field=standardfield('subject'),
                                      order=6,
                                      value=tag)
        if url:
            FieldValue.objects.create(record=record,
                                      field=standardfield('source'),
                                      order=7,
                                      value=url)

        CollectionItem.objects.create(collection=collection, record=record)

        # create job to download actual media file
        from .tasks import flickr_download_media
        flickr_download_media.delay(record.id, image_url)

        return record

    @classmethod
    def available(cls):
        return bool(settings.FLICKR_KEY) and bool(settings.FLICKR_SECRET)
