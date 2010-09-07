from django.utils import simplejson
from rooibos.data.models import Record
from rooibos.storage.models import Media
from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
from rooibos.federatedsearch.nasa import NasaImageExchange
from rooibos.util import guess_extension
import logging
import mimetypes
import urllib2
import traceback

@register_worker('nasa_download_media')
def nasa_download_media(job):

    logging.info('nasa_download_media started for %s' % job)
    jobinfo = JobInfo.objects.get(id=job.arg)

    try:
        if jobinfo.status.startswith == 'Complete':
            # job finished previously
            return
        nasa = NasaImageExchange()
        arg = simplejson.loads(jobinfo.arg)
        record = Record.objects.get(id=arg['record'], manager='nasaimageexchange')
        url = arg['url']
        storage = nasa.get_storage()
        file = urllib2.urlopen(url)
        setattr(file, 'size', int(file.info().get('content-length')))
        mimetype = file.info().get('content-type')
        media = Media.objects.create(record=record,
                             storage=storage,
                             name=record.name,
                             mimetype=mimetype)
        media.save_file(record.name + guess_extension(mimetype), file)
        jobinfo.complete('Complete', 'File downloaded')
        
    except Exception, ex:
        
        logging.info('nasa_download_media failed for %s (%s)' % (job, ex))
        jobinfo.update_status('Failed: %s' % ex)
            
