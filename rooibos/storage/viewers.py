from django import forms
from django.http import Http404
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from rooibos.access import get_effective_permissions_and_restrictions, filter_by_access
from rooibos.viewers import register_viewer, Viewer
from rooibos.data.models import Record
from models import Storage
import re


SUPPORTED_MIMETYPES = (
    'video/mp4',
    'video/quicktime',
    'video/x-m4v',
    'video/x-flv',
    'audio/mpeg',
    'audio/x-aac',
    )

def _supported_media(obj, user):
    return obj.media_set.filter(
                storage__in=filter_by_access(user, Storage),
                mimetype__in=SUPPORTED_MIMETYPES,
                )


def _check_playable(user, media):
    restrictions = get_effective_permissions_and_restrictions(user, media.storage)[3]
    return not restrictions or restrictions.get('download') != 'only'


class MediaPlayer(Viewer):

    title = "Media Player"
    weight = 20
    is_embeddable = True

    def get_options_form(self):

        def media_label(media):
            dimension = (('%sx%s ' % (media.width, media.height))
                         if media.width and media.height
                         else '')
            bitrate = (('at %s kbps ' % media.bitrate)
                       if media.bitrate
                       else '')
            return 'Media: %s%sin %s' % (dimension,
                                         bitrate,
                                         media.storage.title)

        def media_choices():
            return (('', 'default'),) + tuple((media.id, media_label(media))
                for media in _supported_media(self.obj, self.user))

        class OptionsForm(forms.Form):
            media = forms.ChoiceField(choices=media_choices(), required=False)
            autoplay = forms.BooleanField(required=False)

        return OptionsForm

    def embed_script(self, request):

        autoplay = request.GET.get('autoplay', 'False') == 'True'
        media_id = request.GET.get('media', '0')
        divid = request.GET.get('id', 'unknown')

        media = _supported_media(self.obj, request.user).order_by('bitrate')
        if media_id and media_id != '0':
            media = media.filter(id=media_id)
        media = [m for m in media if _check_playable(request.user, m)]
        if not media:
            raise Http404()

        selectedmedia = media[0]
        delivery_url = selectedmedia.get_delivery_url()
        streaming_server = None
        streaming_media = None

        server = (('https' if request.META.get('HTTPS', 'off') == 'on' else 'http') +
            '://' + request.META['HTTP_HOST'])

        if delivery_url.startswith('rtmp://'):
            try:
                streaming_server, prot, streaming_media = re.split('/(mp[34]:)', delivery_url)
                streaming_media = prot + re.sub(r'\.mp3$', '', streaming_media)
            except ValueError:
                pass
        if not '://' in delivery_url:
            delivery_url = server + delivery_url

        return render_to_response('storage_mediaplayer.js',
                                  {'record': self.obj,
                                   'selectedmedia': selectedmedia,
                                   'delivery_url': delivery_url,
                                   'streaming_server': streaming_server,
                                   'streaming_media': streaming_media,
                                   'audio': selectedmedia.mimetype.startswith('audio/'),
                                   'server_url': server,
                                   'autoplay': autoplay,
                                   'flowplayer_key': getattr(settings, "FLOWPLAYER_KEY", None),
                                   'anchor_id': divid,
                                   },
                                  context_instance=RequestContext(request))


@register_viewer('mediaplayer', MediaPlayer)
def mediaplayer(obj, request, objid=None):
    if obj:
        if not isinstance(obj, Record):
            return None
    else:
        try:
            obj = Record.get_or_404(objid, request.user)
        except Http404:
            return None
    media = _supported_media(obj, request.user)
    return MediaPlayer(obj, request.user) if any(_check_playable(request.user, m) for m in media) else None
