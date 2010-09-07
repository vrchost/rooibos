from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from rooibos.presentation.models import Presentation
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.access import accessible_ids


class ViewPresentation(object):

    title = "View"
    weight = 100
    
    def __init__(self):
        pass
    
    def analyze(self, obj, user):
        if not isinstance(obj, Presentation):
            return NO_SUPPORT
        items = obj.cached_items()
        valid = filter(lambda i: not i.type or i.hidden, items)
        if len(valid) == 0:
            return NO_SUPPORT
        elif len(valid) < len(items):
            return PARTIAL_SUPPORT
        else:
            return FULL_SUPPORT
    
    def url(self):
        return url(r'^view/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.view, name='viewers-view')
    
    def url_for_obj(self, obj):
        return reverse('viewers-view', kwargs={'id': obj.id, 'name': obj.name})
    
    def view(self, request, id, name):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        presentation = Presentation.get_by_id_for_request(id, request)
        if not presentation:
            return HttpResponseRedirect(return_url)
        
        return render_to_response('presentations/mediaviewer.html',
                                  {'presentation': presentation,
                                   'return_url': return_url,
                                },
                            context_instance=RequestContext(request))
