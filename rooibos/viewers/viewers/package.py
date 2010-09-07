from rooibos.presentation.models import Presentation
from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT


class PackagePresentation(object):

    title = "Package"
    weight = 10
    
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
        return url(r'^package/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.package, name='viewers-package')
    
    def url_for_obj(self, obj):
        return reverse('viewers-package', kwargs={'id': obj.id, 'name': obj.name})
    
    def package(self, request, id, name):
        return HttpResponse(content='Packaging of presentation %s goes here!' % name)