from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from urllib.request import urlopen
from urllib.error import HTTPError
from .localfs import LocalFileSystemStorageSystem
from rooibos.storage.functions import get_media_for_record


class PseudoStreamingStorageSystem(LocalFileSystemStorageSystem):

    def __init__(self, base=None, storage=None):
        LocalFileSystemStorageSystem.__init__(self, base, storage)

    def get_absolute_media_url(self, media):
        return reverse(
            'storage-retrieve-pseudostream',
            kwargs={
                'recordid': media.record.id,
                'record': media.record.name,
                'mediaid': media.id,
                'media': media.name
            }
        )

    def get_absolute_file_path(self, media):
        return self.path(media.url)

    def open(self, *args, **kwargs):
        # Direct file download not supported
        return None


def retrieve_pseudostream(request, recordid, record, mediaid, media):

    mediaobj = get_media_for_record(recordid, request.user).get(id=mediaid)

    q = dict()
    start = request.GET.get('start', '')
    if start.isdigit():
        q['start'] = start
    end = request.GET.get('end', '')
    if end.isdigit():
        q['end'] = end
    client = request.GET.get('client')
    if client:
        q['client'] = client

    url = mediaobj.storage.urlbase
    url = url + ('/' if not url.endswith('/') else '') + \
        mediaobj.url.replace('\\', '/')
    if q:
        url = url + '?' + urlencode(q)

    try:
        result = urlopen(url)
        response = HttpResponse(
            FileWrapper(result),
            content_type=result.info().get('Content-Type')
        )
        response['Content-Length'] = result.info().get('Content-Length')
        return response
    except HTTPError as e:
        return HttpResponse(status=e.errno)
