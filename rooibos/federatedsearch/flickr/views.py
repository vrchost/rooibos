from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
import json as simplejson
from rooibos.data.models import Record
from .search import FlickrSearch
import math
from django.utils.http import urlencode
from rooibos.ui.views import select_record


@login_required
def search(request):

    pagesize = 30  # per Flickr API TOS

    query = request.GET.get('q', '') or request.POST.get('q', '')
    try:
        page = int(request.GET.get('p', 1))
    except ValueError:
        page = 1

    f = FlickrSearch()
    results = f.search(query, page, pagesize) if query else None

    if results['records']:
        # Map URLs to IDs and find out which ones are already selected
        urls = [r['record_url'] for r in results['records']]
        ids = dict(
            Record.objects.filter(source__in=urls, manager='flickr')
            .values_list('source', 'id')
        )
        selected = request.session.get('selected_records', ())

        for r in results['records']:
            r['id'] = ids.get(r['record_url'])
            r['selected'] = r['id'] in selected

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
        'flickr-results.html',
        {
            'query': query,
            'results': results,
            'page': page,
            'pages': pages,
            'prev_page': prev_page_url,
            'next_page': next_page_url,
        }
    )


def flickr_select_record(request):

    if not request.user.is_authenticated():
        raise Http404()

    if request.method == "POST":
        f = FlickrSearch()
        remote_ids = simplejson.loads(request.POST.get('id', '[]'))

        # find records that already have been created for the given URLs
        ids = dict(
            Record.objects.filter(source__in=remote_ids, manager='flickr')
            .values_list('source', 'id')
        )
        result = []
        for remote_id in remote_ids:
            id = ids.get(remote_id)
            if id:
                result.append(id)
            else:
                record = f.create_record(remote_id)
                result.append(record.id)
        # rewrite request and submit to regular selection code
        r = request.POST.copy()
        r['id'] = simplejson.dumps(result)
        request.POST = r

    return select_record(request)
