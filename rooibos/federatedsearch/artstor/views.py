import urllib, urllib2, time
from os import makedirs
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates
from rooibos.solr import SolrIndex
from models import ArtstorSearch
from django.utils import simplejson
from rooibos.util import json_view

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

def main(request):
    return render_to_response('artstor_main.html', {},
                              context_instance=RequestContext(request))

def authorize(request):
    return render_to_response('artstor_main.html', {},
                              context_instance=RequestContext(request))

def photo_search(request):
    search = ArtstorSearch()
    search_string = request.POST.get("search_string", "")
    search_page = request.POST.get("search_page", 1)
    view = request.POST.get("view", "thumb")
    sort = 'relevance'
    if request.POST.get("interesting"):
        sort = 'interestingness-desc'
    results = search.photoSearch(search_string,search_page)

    return render_to_response('artstor_photo_search.html',  {'results':results,'search_string':search_string,'search_page':search_page,'sort':sort,'view':view},
                                      context_instance=RequestContext(request))

@json_view
def select_artstor(request):
    pass
    #ids = map(None, request.POST.getlist('id'))
    #checked = request.POST.get('checked') == 'true'
    #selected = request.session.get('selected_artstors', ())
    #if checked:
    #    selected = set(selected) | set(ids)
    #else:
    #    selected = set(selected) - set(ids)
    #
    #result = []
    #for artstor in selected:
    #    info = artstor.split('|')
    #    result.append(dict(id=int(info[0]), title=info[1]))
    #
    #request.session['selected_artstor'] = selected
    #return dict(status=session_status_rendered(RequestContext(request)), artstors=result, num_selected=len(result))
