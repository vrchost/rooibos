import flickrapi
import urllib, urllib2, time
from os import makedirs
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates
from rooibos.solr import SolrIndex
from rooibos.access.models import AccessControl
from django.conf import settings
from rooibos.federatedsearch.models import FederatedSearch

class FlickrSearch(FederatedSearch):

    def __init__(self):
        self.flickr = flickrapi.FlickrAPI(settings.FLICKR_KEY, settings.FLICKR_SECRET, cache=True, store_token=False)

    def hits_count(self, keyword):
        results = self.flickr.flickr_call(method='flickr.photos.search',
                                          text=keyword,
                                          api_key=settings.FLICKR_KEY,
                                          format='xmlnode',
                                          page=1,
                                          per_page=1,
                                          extras='url_t,path_alias',
                                          sort='date-posted-desc')
        return int(results.photos[0]['total'])
        
    def get_label(self):
        return "Flickr"
    
    def get_search_url(self):
        return ""

    def get_source_id(self):
        return "Flickr"



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

