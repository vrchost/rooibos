from django.utils import simplejson
from rooibos.storage.models import Media, Storage
from rooibos.data.models import Collection
from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
from rooibos.storage import match_up_media
import logging
import mimetypes
import traceback
import os

@register_worker('storage_match_up_media')
def storage_match_up_media_job(job):

    logging.info('storage_match_up_media started for %s' % job)
    jobinfo = JobInfo.objects.get(id=job.arg)

    arg = simplejson.loads(jobinfo.arg)

    logging.info('Matching up media with arguments %s', arg)

    storage = Storage.objects.get(id=arg['storage'])
    collection = Collection.objects.get(id=arg['collection'])

    jobinfo.update_status('Analyzing available files')

    count = -1
    for count, (record, filename) in enumerate(match_up_media(storage, collection)):
        id = os.path.splitext(os.path.split(filename)[1])[0]
        mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        media = Media.objects.create(record=record,
                                     name=id,
                                     storage=storage,
                                     url=filename,
                                     mimetype=mimetype)
        if (count % 100 == 0):
            jobinfo.update_status('Created %s media objects' % (count + 1))

    logging.info('storage_match_up_media complete: %s' % job)
    jobinfo.complete('Complete', '%s files were matched up with existing records.' % (count + 1))
