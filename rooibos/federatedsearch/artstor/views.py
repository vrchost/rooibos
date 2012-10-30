from . import ArtstorSearch
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.http import urlencode
import urllib2
import math


@login_required
def search(request):

    pagesize = 50

    query = request.GET.get('q', '') or request.POST.get('q', '')
    try:
        page = int(request.GET.get('p', 1))
    except ValueError:
        page = 1

    a = ArtstorSearch()

    try:
        results = a.search(query, page, pagesize) if query else None
        failure = False
    except urllib2.HTTPError:
        results = None
        failure = True


    pages = int(math.ceil(float(results['hits']) / pagesize)) if results else 0
    prev_page_url = "?" + urlencode((('q', query), ('p', page - 1))) if page > 1 else None
    next_page_url = "?" + urlencode((('q', query), ('p', page + 1))) if page < pages else None

    return render_to_response('artstor-results.html',
                          {'query': query,
                           'results': results,
                           'page': page,
                           'failure': failure,
                           'pages': pages,
                           'prev_page': prev_page_url,
                           'next_page': next_page_url,
                           },
                          context_instance=RequestContext(request))

