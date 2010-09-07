from __future__ import with_statement
from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from rooibos.access import accessible_ids, accessible_ids_list, check_access, filter_by_access
from rooibos.data.models import Record, Collection, standardfield, get_system_field
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.storage.models import Storage
from rooibos.util import json_view


class AudioTextSync(object):

    title = "Audio Text Sync"
    weight = 40

    def __init__(self):
        pass

    def analyze(self, obj, user):
        if not isinstance(obj, Record):
            return NO_SUPPORT

        storages = filter_by_access(user, Storage)

        has_text = has_audio = False
        for media in obj.media_set.filter(master=None, storage__in=storages):
            if media.mimetype == 'audio/mpeg':
                has_audio = True
            elif media.mimetype == 'text/plain':
                has_text = True

        return FULL_SUPPORT if has_audio and has_text else NO_SUPPORT

    def url(self):
        return [
            url(r'^audiotextsync/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.view, name='viewers-audiotextsync'),
            url(r'^audiotextsync/(?P<id>[\d]+)/(?P<name>[-\w]+)/setmarker/$', self.set_marker, name='viewers-audiotextsync-setmarker'),
            ]

    def url_for_obj(self, obj):
        return reverse('viewers-audiotextsync', kwargs={'id': obj.id, 'name': obj.name})


    def _get_record_and_access(self, request, id, name):
        record = Record.get_or_404(id, request.user)
        can_edit = request.user.is_authenticated() and (
            # checks if current user is owner:
            check_access(request.user, record, write=True) or
            # or if user has write access to collection:
            accessible_ids(request.user, record.collection_set, write=True).count() > 0)
        return (record, can_edit)


    def _get_markers(self, record):
        markers, created = record.fieldvalue_set.get_or_create(
            field=get_system_field(),
            label='audio-text-sync-markers',
            defaults=dict(
                hidden=True,
            )
        )
        return markers

    def view(self, request, id, name, template='audiotextsync/audiotextsync.html'):
        next = request.GET.get('next')
        record, can_edit = self._get_record_and_access(request, id, name)
        storages = filter_by_access(request.user, Storage)

        textmedia = audiomedia = None
        for media in record.media_set.filter(master=None, storage__in=storages):
            if not audiomedia and media.mimetype == 'audio/mpeg':
                audiomedia = media
            elif not textmedia and media.mimetype == 'text/plain':
                textmedia = media
        if not textmedia or not audiomedia:
            raise Http404()

        transcript = textmedia.load_file().readlines()
        markers = self._get_markers(record)

        return render_to_response(template,
                                  {'record': record,
                                   'next': next,
                                   'transcript': transcript,
                                   'markers': dict(map(lambda v: v.split(','), markers.value.split())) if markers.value else dict(),
                                   'mp3url': audiomedia.get_absolute_url(),
                                   'edit': can_edit,
                                   },
                                  context_instance=RequestContext(request))


    def set_marker(self, request, id, name):
        @json_view
        def json_set_marker(request, id, name):
            if request.method == "POST":
                index = request.POST['index']
                time = request.POST['time']
                if index and time:
                    record, can_edit = self._get_record_and_access(request, id, name)
                    markers = self._get_markers(record)
                    m = dict(map(lambda v: v.split(','), markers.value.split())) if markers.value else dict()
                    m[index] = time
                    to_remove = []
                    prev_val = None
                    for key in sorted(m.keys()):
                        if prev_val:
                            if prev_val >= m[key]:
                                to_remove.append(key)
                        else:
                            prev_val = m[key]
                    for key in to_remove:
                        del m[key]
                    markers.value = '\n'.join('%s,%s' % (v,k) for v,k in m.iteritems())
                    markers.save()
                    return dict(message="Marker saved.")
                else:
                    return dict(result="Error", message="Missing parameters")
            else:
                return dict(result="Error", message="Invalid method. Use POST.")
        return json_set_marker(request, id, name)
