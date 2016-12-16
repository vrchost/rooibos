import json as simplejson
from rooibos.data.models import Record
from rooibos.storage.models import Media
from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
from rooibos.federatedsearch.shared import SharedSearch
from rooibos.util import guess_extension
from StringIO import StringIO
import logging
import requests


@register_worker('shared_download_media')
def shared_download_media(job):

    logging.info('shared_download_media started for %s' % job)
    jobinfo = JobInfo.objects.get(id=job.arg)

    try:
        if jobinfo.status.startswith == 'Complete':
            # job finished previously
            return
        arg = simplejson.loads(jobinfo.arg)
        shared = SharedSearch(arg['shared_id'])
        record = Record.objects.get(id=arg['record'],
                                    manager=shared.get_source_id())
        url = arg['url']
        storage = shared.get_storage()

        username = shared.shared.username
        password = shared.shared.password

        # do an authenticated request if we have a username and password
        if username and password:
            r = requests.get(url, auth=(username, password))
        else:
            r = requests.get(url)

        # turn our conent into a "file-like" object :)
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
        jobinfo.complete('Complete', 'File downloaded')

    except Exception, ex:

        logging.info('shared_download_media failed for %s (%s)' % (job, ex))
        jobinfo.update_status('Failed: %s' % ex)
