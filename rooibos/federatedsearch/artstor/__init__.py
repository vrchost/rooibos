import urllib, urllib2, time, cookielib, math
from django.utils import simplejson
from os import makedirs
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr import SolrIndex
from rooibos.access.models import AccessControl
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError
from django.conf import settings
from django.core.urlresolvers import reverse
from rooibos.federatedsearch.models import FederatedSearch, HitCount
from BeautifulSoup import BeautifulSoup
import cookielib
import datetime
import socket


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


class ArtstorSearch(FederatedSearch):

    def hits_count(self, keyword):
        url = '%s?%s' % (
            settings.ARTSTOR_GATEWAY,
            urllib.urlencode([('query', 'cql.serverChoice = "%s"' % keyword),
                              ('operation', 'searchRetrieve'),
                              ('version', '1.1'),
                              ('maximumRecords', '1')])
        )
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()), SmartRedirectHandler())
        request = urllib2.Request(url)
        socket.setdefaulttimeout(self.timeout)
        try:
            response = opener.open(request)
        except urllib2.URLError:
            return 0
        soup = BeautifulSoup(response)
        try:
            return int(soup.find('numberofrecords').contents[0])
        except:
            return 0


    def get_label(self):
        return "ARTstor"

    def get_search_url(self):
        return reverse('artstor-search')

    def get_source_id(self):
        return "ARTstor"


    def search(self, keyword, page=1, pagesize=50):
        if not keyword:
            return None
        cached, created = HitCount.current_objects.get_or_create(
            source=self.get_source_id(), query='%s [%s:%s]' % (keyword, page, pagesize),
            defaults=dict(hits=0, valid_until=datetime.datetime.now() + datetime.timedelta(1)))
        if not created and cached.results:
            return simplejson.loads(cached.results)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
                                      SmartRedirectHandler())
        url = '%s?query="%s"&operation=searchRetrieve&version=1.1&maximumRecords=%s&startRecord=%s' % (
            settings.ARTSTOR_GATEWAY,
            urllib.quote(keyword),
            pagesize,
            (page - 1) * pagesize + 1,
        )
        socket.setdefaulttimeout(self.timeout)
        try:
            response = opener.open(urllib2.Request(url))
        except urllib2.URLError:
            return None

        try:
            results = ElementTree(file=response)
            total = results.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords') or 0
        except ExpatError:
            total = 0
        if not total:
            return None

        pages = int(math.ceil(float(total) / pagesize))

        result = dict(records=[], hits=total)
        for image in results.findall('//{info:srw/schema/1/dc-v1.1}dc'):
            for ids in image.findall('{http://purl.org/dc/elements/1.1/}identifier'):
                if ids.text.startswith('URL'):
                    url = ids.text[len('URL:'):]
                elif ids.text.startswith('THUMBNAIL'):
                    tn = ids.text[len('THUMBNAIL:'):]
                else:
                    id = ids.text
            title = image.findtext('{http://purl.org/dc/elements/1.1/}title')
            result['records'].append(dict(
                thumb_url=tn,
                title=title,
                record_url=url))

        cached.results = simplejson.dumps(result, separators=(',', ':'))
        cached.save()
        return result

    @classmethod
    def available(cls):
        return bool(settings.ARTSTOR_GATEWAY)
