from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.http import urlencode
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from urllib2 import urlopen, HTTPError
from localfs import LocalFileSystemStorageSystem
from models import Media, Storage
from rooibos.access import accessible_ids
from rooibos.data.models import Collection


class PseudoStreamingStorageSystem(LocalFileSystemStorageSystem):

    def __init__(self, base=None):
        LocalFileSystemStorageSystem.__init__(self, base)

    def get_absolute_media_url(self, storage, media):
        return reverse('storage-retrieve-pseudostream', kwargs={'recordid': media.record.id,
                                                   'record': media.record.name,
                                                   'mediaid': media.id,
                                                   'media': media.name})

    def get_absolute_file_path(self, storage, media):
        return self.path(media.url)

    def open(self, *args, **kwargs):
        # Direct file download not supported
        return None


def retrieve_pseudostream(request, recordid, record, mediaid, media):

    mediaobj = get_object_or_404(Media.objects.filter(id=mediaid,
                                 record__id=recordid,
                                 record__collection__id__in=accessible_ids(request.user, Collection),
                                 storage__id__in=accessible_ids(request.user, Storage)).distinct())

    q = dict()
    start = request.GET.get('start', '')
    if start.isdigit(): q['start'] = start
    end = request.GET.get('end', '')
    if end.isdigit(): q['end'] = end
    client = request.GET.get('client')
    if client: q['client'] = client

    url = mediaobj.storage.urlbase
    url = url + ('/' if not url.endswith('/') else '') + mediaobj.url.replace('\\', '/')
    if q:
        url = url + '?' + urlencode(q)

    try:
        result = urlopen(url)
        response = HttpResponse(FileWrapper(result), content_type=result.info().get('Content-Type'))
        response['Content-Length'] = result.info().get('Content-Length')
        return response
    except HTTPError, e:
        return HttpResponse(status=e.errno)
