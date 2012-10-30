from django.utils.html import strip_tags


class PageTitles:

    def process_view(self, request, view_func, view_args, view_kwargs):
        return None

    def process_request(self, request):
        pass

    def process_response(self, request, response):

        def _find_tag(c, tag):
            start = c.find('<%s>' % tag)
            if start > -1:
                start += len(tag) + 2
                end = c.find('</%s>' % tag, start)
                if end > -1:
                    return (start, end)
            return None

        if response.status_code == 200 and response.get('Content-Type', '').startswith('text/html'):
            # If the page contains Unicode characters, not converting this to Unicode
            # will cause runtime errors as strip_tags forces Unicode.
            c = unicode(response.content, 'utf8')
            title = _find_tag(c, 'title')
            if title and response.content[title[0]:title[1]] == "MDID":
                heading = _find_tag(c, 'h1')
                if heading:
                    response.content = "%sMDID - %s%s" % (c[:title[0]],
                                                          strip_tags(c[heading[0]:heading[1]]),
                                                          c[title[1]:])
        return response
