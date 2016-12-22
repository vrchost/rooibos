import mimetypes
import os
from rooibos.storage.models import Media, Storage
from rooibos.data.models import Collection
from rooibos.storage import match_up_media
from ..celeryapp import owned_task


@owned_task(removeuserarg=True)
def storage_match_up_media(
        self, storage_id, collection_id, allow_multiple_use):

    storage = Storage.objects.get(id=storage_id)
    collection = Collection.objects.get(id=collection_id)

    count = -1
    created = []
    for count, (record, filename) in enumerate(
            match_up_media(storage, collection, allow_multiple_use)):

        identifier = os.path.splitext(os.path.split(filename)[1])[0]
        mimetype = mimetypes.guess_type(filename)[0] or \
            'application/octet-stream'
        Media.objects.create(
            record=record,
            name=identifier,
            storage=storage,
            url=filename,
            mimetype=mimetype,
        )
        created.append({
            'id': identifier,
            'record': record.id,
            'file': filename,
            'mimetype': mimetype,
        })
        if count % 100 == 99:
            self.update_state(
                state='PROGRESS',
                meta={
                    'count': count + 1,
                }
            )

    return {
        'collection': collection_id,
        'storage': storage_id,
        'allow_multiple_use': allow_multiple_use,
        'count': count + 1,
        'created': created,
    }
