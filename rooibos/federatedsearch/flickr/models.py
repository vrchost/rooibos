import flickrapi
import urllib, urllib2, time
from os import makedirs
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates
from rooibos.solr import SolrIndex
from rooibos.settings import FLICKR_KEY, FLICKR_SECRET
from rooibos.access.models import AccessControl

def _save_file(targeturl, base, filename):
    try:
        req = urllib2.Request(targeturl)
        response = urllib2.urlopen(req)
        try:
            makedirs(base)
        except Exception:
            pass
        image = open('%s/%s' % (base, filename), 'wb')
        image.write(response.read())
        image.close()
    except Exception, detail:
        print 'Error:', detail

class FlickrUploadr:

    flickr = None

    def __init__(self):
        self.flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, cache=False, store_token=False)

    def flickrInstance(self):
        return self.flickr

    def flickr_callback(progress, done):
        if done:
            return done
        else:
            return progress

    def uploadImage(self, imageFilename, imageInfo={"title": "", "description": "", "tags": "", "is_public": 1, "is_friend": 0, "is_family": 0 }
):
        try:
            answer = self.flickr.upload(filename=imageFilename.encode('utf-8'), callabck=self.flickr_callback, title=imageInfo.get("title", "").encode('utf-8'), description=imageInfo.get("description", "").encode('utf-8'), tags=imageInfo.get("tags", "").encode('utf-8'), is_public=imageInfo.get("is_public", 1), is_friend=imageInfo.get("is_friend", 0), is_family=imageInfo.get("is_family", 0))
            return answer
        except Exception, detail:
            return detail
        return

class FlickrSearch:

    flickr = None

    def __init__(self):
        self.flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, cache=True, store_token=False)

    def flickrInstance(self):
        return self.flickr

    def photoSearch(self, searchString="", page=1, sort='date-posted-desc', private="0", token="", perpage=50):
        total = 0
        private_total = 0
        if searchString == "":
            return {"total": int(0), "page": int(0), "pages": int(0), "per_page": int(0), "photos": {}}
        try:
            results = self.flickr.flickr_call(method='flickr.photos.search', text=searchString, api_key=FLICKR_KEY, format='xmlnode', page=page, per_page=perpage, extras='url_t,path_alias', sort=sort)
            public_total = int(results.photos[0]['total'])
            if private == 1:
                results_user = self.flickr.flickr_call(method="flickr.auth.checkToken",api_key=FLICKR_KEY,auth_token=token, format='xmlnode')
                user_id = str(results_user.auth[0].user[0]['nsid'])
                results_private = self.flickr.flickr_call(method='flickr.photos.search', text=searchString, api_key=FLICKR_KEY, format='xmlnode', page=page, per_page=perpage, extras='url_t,path_alias', sort=sort, user_id=user_id)
                private_total = int(results_private.photos[0]['total'])
        except Exception, detail:
          print "Error: "+str(detail)
          return {"total": int(0), "page": int(0), "pages": int(0), "per_page": int(0), "photos": {}}

        total = public_total + private_total
        if int(total) == 0:
            return {"total": int(0), "page": int(0), "pages": int(0), "per_page": int(0), "photos": {}}

        page = results.photos[0]['page']
        pages = results.photos[0]['pages']
        per_page = results.photos[0]['perpage']
        raw_photos = results.photos[0].photo

        photos = []

        if int(private_total) > 0:
            raw_photos_private = results_private.photos[0].photo
            for photo in raw_photos_private:
                if photo['title'] == "":
                    photo['title'] = 'None'
                photos.append({'id': photo['id'], 'title': photo['title'], 'thumb': photo['url_t'], 'photo_page': "http://www.flickr.com/photos/" + photo['owner'] + "/" + photo['id']})

        if int(public_total) > 0:
            for photo in raw_photos:
                if photo['title'] == "":
                    photo['title'] = 'None'
                photos.append({'id': photo['id'], 'title': photo['title'], 'thumb': photo['url_t'], 'photo_page': "http://www.flickr.com/photos/" + photo['owner'] + "/" + photo['id']})

        return {"total": int(total), "page": int(page), "pages": int(pages), "per_page": int(per_page), "photos": photos}

class FlickrImportr:

    flickr = None

    def __init__(self):
        self.flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, cache=False, store_token=False)

    def flickrInstance(self):
        return self.flickr

    def getOriginalPhoto(self, photoId):
        info = []
        try:
            info = self.flickr.flickr_call(method='flickr.photos.getSizes', api_key=FLICKR_KEY, format='xmlnode', photo_id=photoId)
        except Exception, detail:
            return []

        sizes = info.sizes[0]
        original_size = sizes.size[len(sizes.size) - 1]
        return dict(label=original_size['label'], width=original_size['width'], height=original_size['height'], source=original_size['source'])

    def importPhoto(self, photoId, title):
        originalInfo = self.getOriginalPhoto(photoId)

        collection, created = Collection.objects.get_or_create(title='flickr Import', name='flickr-import')
        if created:
            collection.save()

        storage = Storage.objects.get(name='personal-images-full')

        record = Record()
        record.name = originalInfo['source'].split('/')[-1].split('.')[0]
        record.save(force_insert=True)
        CollectionItem.objects.create(record=record, collection=collection).save()

        AccessControl.objects.create(content_object=record, read=True)
        dc_identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        dc_title = Field.objects.get(name='title', standard__prefix='dc')
        record.fieldvalue_set.create(field=dc_identifier, value=photoId)
        record.fieldvalue_set.create(field=dc_title, value=title)
        record.save()

        media = Media(record=record,
                      name='full',
                      url=originalInfo['source'].split('/')[-1],
                      storage=storage,
                      mimetype='image/jpeg',
                      width=originalInfo['width'],
                      height=originalInfo['height'])
        media.save()
        _save_file(originalInfo['source'], storage.base, originalInfo['source'].split('/')[-1])

        siu = SolrIndexUpdates(record=record.id)
        siu.save()
        return dict(record=record, media=media)

class FlickrSetPhotos:

    flickr = None

    def __init__(self):
        self.flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, cache=True, store_token=False)

    def flickrInstance(self):
        return self.flickr

    def setPhotos(self, setId="", page=1, sort='date-posted-desc', perpage=50):
        if setId == "":
            return {"total": int(0), "page": int(0), "pages": int(0), "per_page": int(0), "photos": {}}
        try:
            results = self.flickr.flickr_call(method='flickr.photosets.getPhotos', photoset_id=setId, api_key=FLICKR_KEY, format='xmlnode', page=page, per_page=perpage, extras='url_t,path_alias', sort=sort)
        except Exception, detail:
          return {"total": int(0), "page": int(0), "pages": int(0), "per_page": int(10), "photos": {}}

        total = results.photoset[0]['total']
        if int(total) == 0:
            return {"total": int(0), "page": int(0), "pages": int(0), "per_page": int(110), "photos": {}}

        page = results.photoset[0]['page']
        pages = results.photoset[0]['pages']
        per_page = results.photoset[0]['perpage']
        owner = results.photoset[0]['owner']
        raw_photos = results.photoset[0].photo
        photos = []
        for photo in raw_photos:
            if photo['title'] == "":
                photo['title'] = 'None'
            photos.append({'id': photo['id'], 'title': photo['title'], 'thumb': photo['url_t'], 'photo_page': "http://www.flickr.com/photos/" + owner + "/" + photo['id']})
        return {"total": int(total), "page": int(page), "pages": int(pages), "per_page": int(per_page), "photos": photos}
