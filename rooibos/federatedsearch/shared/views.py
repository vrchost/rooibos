from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.http import urlencode
import urllib2
import math

import urllib, urllib2, time, cookielib, math
from django.utils import simplejson
from os import makedirs
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates
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
import json
import logging


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


class SharedSearch(FederatedSearch):

    def hits_count(self, keyword):
        shared_collections = getattr(settings, 'SHARED_COLLECTIONS', None)
        if not shared_collections:
            return 0
        shared = shared_collections['Test']
        
        url = "%s?%s" % (shared['url'],
                          urllib.urlencode([('kw', keyword)]))
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()), SmartRedirectHandler())
        request = urllib2.Request(url)
        
        import base64
        base64string = base64.encodestring('%s:%s' % (shared['username'], shared['password']))[:-1]
        request.add_header("Authorization", "Basic %s" % base64string)

        socket.setdefaulttimeout(self.timeout)
        try:
            response = opener.open(request)
            data = json.loads(response.read())
            if data['result'] == 'ok':
                return data['hits']
        except Exception, ex:
            logging.exception('Shared collection search failed')
            return 0
        return 0

    def get_label(self):
        return "Shared"

    def get_search_url(self):
        return reverse('shared-search')

    def get_source_id(self):
        return "Shared"


    def search(self, keyword, page=1, pagesize=30):
        #if not keyword:
        #    return None
        #cached, created = HitCount.current_objects.get_or_create(
        #    source=self.get_source_id(), query='%s [%s:%s]' % (keyword, page, pagesize),
        #    defaults=dict(hits=0, valid_until=datetime.datetime.now() + datetime.timedelta(1)))
        #if not created and cached.results:
        #    return simplejson.loads(cached.results)
        #
        #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
        #                              SmartRedirectHandler())
        #url = '%s?query="%s"&operation=searchRetrieve&version=1.1&maximumRecords=%s&startRecord=%s' % (
        #    settings.ARTSTOR_GATEWAY,
        #    urllib.quote(keyword),
        #    pagesize,
        #    (page - 1) * pagesize + 1,
        #)
        #socket.setdefaulttimeout(self.timeout)
        #try:
        #    response = opener.open(urllib2.Request(url))
        #except urllib2.URLError:
        #    return None
        #
        #try:
        #    results = ElementTree(file=response)
        #    total = results.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords') or 0
        #except ExpatError:
        #    total = 0
        #if not total:
        #    return None
        #
        #pages = int(math.ceil(float(total) / pagesize))
        #
        #result = dict(records=[], hits=total)
        #for image in results.findall('//{info:srw/schema/1/dc-v1.1}dc'):
        #    for ids in image.findall('{http://purl.org/dc/elements/1.1/}identifier'):
        #        if ids.text.startswith('URL'):
        #            url = ids.text[len('URL:'):]
        #        elif ids.text.startswith('THUMBNAIL'):
        #            tn = ids.text[len('THUMBNAIL:'):]
        #        else:
        #            id = ids.text
        #    title = image.findtext('{http://purl.org/dc/elements/1.1/}title')
        #    result['records'].append(dict(
        #        thumb_url=tn,
        #        title=title,
        #        record_url=url))
        #
        #cached.results = simplejson.dumps(result, separators=(',', ':'))
        #cached.save()
        #return result
        return None

    @classmethod
    def available(cls):
        return bool(getattr(settings, 'SHARED_COLLECTIONS', None))



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
    prev_page_url = "?" + urlencode((('q', query), ('p', page - 1))) if page > 1 else None
    next_page_url = "?" + urlencode((('q', query), ('p', page + 1))) if page < pages else None

    return render_to_response('federatedsearch/shared/results.html',
                          {'query': query,
                           'results': results,
                           'page': page,
                           'failure': failure,
                           'pages': pages,
                           'prev_page': prev_page_url,
                           'next_page': next_page_url,
                           },
                          context_instance=RequestContext(request))

