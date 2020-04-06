import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import json as simplejson
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError
from django.conf import settings
from django.core.urlresolvers import reverse
from rooibos.federatedsearch import FederatedSearch
from bs4 import BeautifulSoup
import http.cookiejar
import datetime
import socket


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


class ArtstorSearch(FederatedSearch):

    def hits_count(self, keyword):
        url = '%s?%s' % (
            settings.ARTSTOR_GATEWAY,
            urllib.parse.urlencode([('query', 'cql.serverChoice = "%s"' % keyword),
                              ('operation', 'searchRetrieve'),
                              ('version', '1.1'),
                              ('maximumRecords', '1')])
        )
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(
                http.cookiejar.CookieJar()
            ),
            SmartRedirectHandler()
        )
        request = urllib.request.Request(url)
        socket.setdefaulttimeout(self.timeout)
        try:
            response = opener.open(request)
        except urllib.error.URLError:
            return 0
        soup = BeautifulSoup(response, 'html.parser')
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

        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
            SmartRedirectHandler()
        )
        url = '%s?query="%s"&operation=searchRetrieve&version=1.1&' \
            'maximumRecords=%s&startRecord=%s' % (
                settings.ARTSTOR_GATEWAY,
                urllib.parse.quote(keyword),
                pagesize,
                (page - 1) * pagesize + 1,
            )
        socket.setdefaulttimeout(self.timeout)
        try:
            response = opener.open(urllib.request.Request(url))
        except urllib.error.URLError:
            return None

        try:
            results = ElementTree(file=response)
            total = results.findtext(
                '{http://www.loc.gov/zing/srw/}numberOfRecords') or 0
        except ExpatError:
            total = 0
        if not total:
            return None

        result = dict(records=[], hits=total)
        for image in results.findall('//{info:srw/schema/1/dc-v1.1}dc'):
            for ids in image.findall(
                    '{http://purl.org/dc/elements/1.1/}identifier'):
                if ids.text.startswith('URL'):
                    url = ids.text[len('URL:'):]
                elif ids.text.startswith('THUMBNAIL'):
                    tn = ids.text[len('THUMBNAIL:'):]
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
