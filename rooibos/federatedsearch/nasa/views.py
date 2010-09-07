from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from . import NasaImageExchange
from rooibos.ui.views import select_record
from django.utils import simplejson
from rooibos.data.models import Record


@login_required
def search(request):
    
    query = request.GET.get('q', '') or request.POST.get('q', '')
    n = NasaImageExchange()
    results = n.search(query) if query else None

    # Map URLs to IDs and find out which ones are already selected
    urls = [r['record_url'] for r in results]
    ids = dict(Record.objects.filter(source__in=urls, manager='nasaimageexchange').values_list('source', 'id'))
    selected = request.session.get('selected_records', ())
    
    for r in results:
        r['id'] = ids.get(r['record_url'])
        r['selected'] = r['id'] in selected

    return render_to_response('nasa-nix-results.html',
                          {'query': query,
                           'results': results,
                           'hits': results and len(results) or 0},
                          context_instance=RequestContext(request))


def nix_select_record(request):

    if not request.user.is_authenticated():
        raise Http404()

    if request.method == "POST":
        nix = NasaImageExchange()
        urls = simplejson.loads(request.POST.get('id', '[]'))
        
        # find records that already have been created for the given URLs
        ids = dict(Record.objects.filter(source__in=urls, manager='nasaimageexchange').values_list('source', 'id'))
        result = []
        for url in urls:
            id = ids.get(url)
            if id:
                result.append(id)
            else:
                record = nix.create_record(url)
                result.append(record.id)
        # rewrite request and submit to regular selection code
        r = request.POST.copy()
        r['id'] = simplejson.dumps(result)
        request.POST = r
        
    return select_record(request)
