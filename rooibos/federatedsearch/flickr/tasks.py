import urllib.request, urllib.error, urllib.parse
from io import StringIO

from ...celeryapp import app

from rooibos.data.models import Record
from rooibos.storage.models import Media
from rooibos.storage.functions import rotateImageBasedOnExif
from .search import FlickrSearch
from rooibos.util import guess_extension


@app.task
def flickr_download_media(record_id, url):
    flickr = FlickrSearch()
    record = Record.objects.get(id=record_id, manager='flickr')
    storage = flickr.get_storage()
    file = urllib.request.urlopen(url)
    mimetype = file.info().get('content-type')
    media = Media.objects.create(
        record=record,
        storage=storage,
        name=record.name,
        mimetype=mimetype,
    )
    # should be done better: loading file into StringIO object to make it
    # seekable
    file = StringIO(file.read())
    file = rotateImageBasedOnExif(file)
    media.save_file(record.name + guess_extension(mimetype), file)
