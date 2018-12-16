import mimetypes
import os
import json
from datetime import datetime
from rooibos.storage.models import Media, Storage
from rooibos.data.models import Collection
from rooibos.storage.functions import match_up_media, analyze_media
from rooibos.access.functions import filter_by_access
from django.contrib.auth.models import User
from rooibos.workers.tasks import get_attachment
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

    attachment = get_attachment(self)
    with open(attachment, 'w') as report:
        json.dump(created, report, indent=2)

    return {
        'collection': collection_id,
        'storage': storage_id,
        'allow_multiple_use': allow_multiple_use,
        'count': count + 1,
        'attachment': attachment,
    }


@owned_task()
def analyze_media_task(self, owner, storage_id):
    storage = filter_by_access(
        User.objects.get(id=owner),
        Storage.objects.filter(id=storage_id), manage=True)[0]
    broken, extra = analyze_media(storage, True)
    broken = [m.url for m in broken]
    attachment = get_attachment(self)
    with open(attachment, 'w') as report:
        report.write('Analyze Report for Storage %s (%d)\n\n' % (
            storage.name, storage.id))
        report.write('Created on %s\n\n' % datetime.now())
        report.write('%d MISSING FILES:\n' % len(broken))
        report.write('\n'.join(sorted(broken)))
        report.write('\n\n%d EXTRA FILES:\n' % len(extra))
        report.write('\n'.join(sorted(extra)))
    return {
        'attachment': attachment,
    }
