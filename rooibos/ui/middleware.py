
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
            title = _find_tag(response.content, 'title')
            if title and response.content[title[0]:title[1]] == "MDID":
                heading = _find_tag(response.content, 'h1')
                if heading:
                    response.content = "%sMDID - %s%s" % (response.content[:title[0]],
                                                          response.content[heading[0]:heading[1]],
                                                          response.content[title[1]:])
        return response
    
    