from . import ArtstorSearch
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.http import urlencode
import urllib.request, urllib.error, urllib.parse
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
    except urllib.error.HTTPError:
        results = None
        failure = True

    pages = int(math.ceil(float(results['hits']) / pagesize)) if results else 0
    if page > 1:
        prev_page_url = "?" + urlencode((('q', query), ('p', page - 1)))
    else:
        prev_page_url = None
    if page < pages:
        next_page_url = "?" + urlencode((('q', query), ('p', page + 1)))
    else:
        next_page_url = None

    return render(request,
        'artstor-results.html',
        {
            'query': query,
            'results': results,
            'page': page,
            'failure': failure,
            'pages': pages,
            'prev_page': prev_page_url,
            'next_page': next_page_url,
        }
    )
