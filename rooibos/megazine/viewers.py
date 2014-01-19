from django import forms
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from rooibos.access import get_effective_permissions_and_restrictions, filter_by_access
from rooibos.viewers import register_viewer, Viewer
from rooibos.presentation.models import Presentation
from rooibos.storage.models import Media
import re
import math


class MegazineViewer(Viewer):

    title = "Megazine Viewer"
    weight = 20
    is_embeddable = True

    def get_options_form(self):

        class OptionsForm(forms.Form):
            width = forms.IntegerField(max_value=1600, min_value=600, initial=1000,
                                       help_text="Enter width in pixels between 600 and 1600")

        return OptionsForm


    def embed_script(self, request):

        try:
            width = int(request.GET.get('width', 1000))
        except ValueError:
            width = 1000

        # Calculate required height based on width
        pagewidth = width / 2 - 100
        # get aspect ratio for all items in presentation and find smallest
        # don't need to worry about permissions here, just do a quick calc
        allmedia = Media.objects.filter(
            record__presentationitem__in=self.obj.items.filter(hidden=False))
        # only look at media that have width and height set
        ratio = min(media.width / float(media.height)
                    for media in allmedia
                    if media.width and media.height)
        pageheight = width / ratio

        height = int(math.sqrt(pagewidth * pagewidth +
                               pageheight * pageheight) * 2 - pageheight)

        divid = request.GET.get('id', 'unknown')
        server = (('https' if request.META.get('HTTPS', 'off') == 'on' else 'http') +
            '://' + request.META['HTTP_HOST'])

        return render_to_response('megazine_viewer.js',
                                  {'presentation': self.obj,
                                   'server_url': server,
                                   'anchor_id': divid,
                                   'width': width,
                                   'height': height,
                                   'pagewidth': pagewidth,
                                   'pageheight': pageheight,
                                   # TODO: pass through pagewidth and pageheight
                                   },
                                  context_instance=RequestContext(request))


@register_viewer('megazine', MegazineViewer)
def megazine(obj, request, objid=None):
    if not getattr(settings, 'MEGAZINE_PUBLIC_KEY', None):
        return None
    if obj:
        if not isinstance(obj, Presentation):
            return None
    else:
        obj = Presentation.get_by_id_for_request(objid, request)
        if not obj:
            return None
    return MegazineViewer(obj, request.user)
