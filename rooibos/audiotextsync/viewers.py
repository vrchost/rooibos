from django import forms
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from rooibos.access import get_effective_permissions_and_restrictions, filter_by_access
from rooibos.viewers import register_viewer, Viewer
from rooibos.data.models import Record
from rooibos.storage.models import Storage
from functions import get_markers
import re
import math



class AudioTextSyncViewer(Viewer):

    title = "Audio Text Sync Viewer"
    weight = 10

    def view(self, request, template='audiotextsync_view.html'):
        next = request.GET.get('next')
        can_edit = self.obj.editable_by(request.user)

        textmedia = audiomedia = None
        for media in self.obj.media_set.filter(
            storage__in=filter_by_access(request.user, Storage)):
            if not audiomedia and media.mimetype == 'audio/mpeg':
                audiomedia = media
            elif not textmedia and media.mimetype == 'text/plain':
                textmedia = media
        if not textmedia or not audiomedia:
            raise Http404()
        transcript = textmedia.load_file().readlines()
        markers = get_markers(self.obj)

        return render_to_response(template,
                                  {'record': self.obj,
                                   'next': next,
                                   'transcript': transcript,
                                   'markers': dict(map(lambda v: v.split(','), markers.value.split())) if markers.value else dict(),
                                   'mp3url': audiomedia.get_absolute_url(),
                                   'edit': can_edit,
                                   },
                                  context_instance=RequestContext(request))




@register_viewer('audiotextsyncviewer', AudioTextSyncViewer)
def audiotextsyncviewer(obj, request, objid=None):
    if obj:
        if not isinstance(obj, Record):
            return None
    else:
        obj = Record.filter_one_by_access(request.user, objid)
        if not obj:
            return None
    has_text = has_audio = False
    for media in obj.media_set.filter(
        storage__in=filter_by_access(request.user, Storage)):
        if media.mimetype == 'audio/mpeg':
            has_audio = True
        elif media.mimetype == 'text/plain':
            has_text = True
    if not has_text or not has_audio:
        return None
    return AudioTextSyncViewer(obj, request.user)
