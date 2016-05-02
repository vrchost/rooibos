from django.conf import settings
from django.db import connection
from time import time
from operator import add
import re


class StatsMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        In your base template, put this:
        {% if debug %}  <div id="stats"><!-- STATS: Total: %(totTime).2fs <br/>
        Python: %(pyTime).2fs <br/>
        DB: %(dbTime).2fs <br/>
        Queries: %(queries)d --></div> {% endif %}

        Here's the css style I use:
        #stats { background-color: #ddd; font-size: 65%; padding: 5px;
        z-index: 1000; position: absolute; right: 5px; top: 5px;
        -moz-opacity: .7; opacity: .7;}
        """

        # This stuff will only happen if debug is already on
        if not settings.DEBUG:
            return None

        # get number of db queries before we do anything
        n = len(connection.queries)

        # time the view
        start = time()
        response = view_func(request, *view_args, **view_kwargs)
        ct = response.get('content-type', None)
        if not (ct and ct.startswith('text/html')):
            return response

        tot_time = time() - start

        # compute the db time for the queries just run
        queries = len(connection.queries) - n
        if queries:
            db_time = reduce(
                add, [float(q['time']) for q in connection.queries[n:]])
        else:
            db_time = 0.0

        # and backout python time
        py_time = tot_time - db_time

        stats = {
            'totTime': tot_time,
            'pyTime': py_time,
            'dbTime': db_time,
            'queries': queries,
        }

        # replace the comment if found
        if response and response.content:
            s = response.content
            regexp = re.compile(r'(?P<cmt><!--\s*STATS:(?P<fmt>.*?)-->)')
            match = regexp.search(s)
            if match:
                s = s[:match.start('cmt')] + \
                    match.group('fmt') % stats + \
                    s[match.end('cmt'):]
                response.content = s

        return response
