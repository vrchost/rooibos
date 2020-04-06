from django.template import RequestContext
from django.template.loader import render_to_string
from rooibos.util import json_view
from datetime import datetime, timedelta
from threading import Thread
from .models import HitCount

from .artstor import ArtstorSearch
from .flickr.search import FlickrSearch
from .shared.views import SharedSearch

import logging


source_classes = [
    ArtstorSearch,
    FlickrSearch,
    SharedSearch,
]


def available_federated_sources(user):
    for c in source_classes:
        if hasattr(c, 'get_instances'):
            for i in c.get_instances(user):
                yield i
        elif c.available():
            yield c()


def sidebar_api_raw(request, query, cached_only=False):

    sources = dict(
        (s.get_source_id(), s)
        for s in available_federated_sources(request.user)
    )

    if not sources:
        return dict(html='', hits=0)

    if not request.user.is_authenticated():
        return dict(html="Please log in to see additional content.", hits=0)

    if not query:
        return dict(
            html='Please specify at least one search criteria '
            'to find additional content.',
            hits=0
        )

    cache = dict(
        HitCount.current_objects.filter(
            query=query, source__in=list(sources.keys())
        ).values_list('source', 'hits')
    )

    class HitCountThread(Thread):

        def __init__(self, source):
            super(HitCountThread, self).__init__()
            self.source = source
            self.hits = 0
            self.instance = None
            self.cache_hit = False

        def run(self):
            self.instance = sources[self.source]
            if self.source in cache:
                self.cache_hit = True
                if cache[self.source]:
                    self.hits = cache[self.source]
            elif not cached_only:
                try:
                    self.hits = self.instance.hits_count(query)
                    HitCount.objects.create(
                        query=query,
                        source=self.source,
                        hits=self.hits,
                        valid_until=datetime.now() + timedelta(1)
                    )
                except Exception:
                    logging.exception("Federated Search")
                    self.hits = -1

    threads = []
    for source in sorted(sources.keys()):
        thread = HitCountThread(source)
        threads.append(thread)
        thread.start()

    results = []
    total_hits = 0
    cache_hit = True
    for thread in threads:
        thread.join()
        cache_hit = cache_hit and thread.cache_hit
        if thread.hits:
            if thread.hits > 0:
                total_hits += thread.hits
            results.append((thread.instance, thread.hits))

    return dict(
        html=render_to_string(
            'federatedsearch_results.html',
            dict(
                results=sorted(results),
                query=query
            ),
            request=request,
        ),
        hits=total_hits,
        cache_hit=cache_hit
    )


@json_view
def sidebar_api(request):
    query = ' '.join(request.GET.get('q', '').strip().lower().split())
    return sidebar_api_raw(request, query)
