from ...celeryapp import app

from rooibos.data.models import Record
from rooibos.storage.models import Media
from .views import SharedSearch
from rooibos.util import guess_extension
from io import StringIO
import requests


@app.task
def shared_download_media(shared_id, record_id, url):
    shared = SharedSearch(shared_id)
    record = Record.objects.get(
        id=record_id,
        manager=shared.get_source_id(),
    )
    storage = shared.get_storage()

    username = shared.shared.username
    password = shared.shared.password

    # do an authenticated request if we have a username and password
    if username and password:
        r = requests.get(url, auth=(username, password))
    else:
        r = requests.get(url)

    # turn our content into a "file-like" object
    file = StringIO(r.content)
    setattr(file, 'size', int(r.headers['content-length']))
    mimetype = r.headers['content-type']

    media = Media.objects.create(
        record=record,
        storage=storage,
        name=record.name,
        mimetype=mimetype,
    )
    media.save_file(record.name + guess_extension(mimetype), file)
