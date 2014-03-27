from __future__ import with_statement
from django.utils import simplejson
from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
from rooibos.data.models import Collection, FieldSet
import logging
import os
import csv
from spreadsheetimport import SpreadsheetImport
from views import _get_scratch_dir


@register_worker('csvimport')
def csvimport(job):

    logging.debug('csvimport started for %s' % job)
    jobinfo = JobInfo.objects.get(id=job.arg)

    try:

        arg = simplejson.loads(jobinfo.arg)

        if jobinfo.status.startswith == 'Complete':
            # job finished previously
            logging.debug('csvimport finished previously for %s' % job)
            return

        file = os.path.join(_get_scratch_dir(), arg['file'])
        if not os.path.exists(file):
            # import file missing
            jobinfo.complete('Import file missing', 'Import failed')

        resultfile = file + '.result'
        if os.path.exists(resultfile):
            # import must have died in progress
            with open(resultfile, 'r') as f:
                results = csv.DictReader(f)
                count = -1
                for count, row in enumerate(results):
                    pass
            skip_rows = count + 1
        else:
            skip_rows = 0

        infile = open(file, 'rU')
        outfile = open(resultfile, 'a', 0)
        outwriter = csv.writer(outfile)

        if not skip_rows:
            outwriter.writerow(['Identifier', 'Action'])

        class Counter(object):
            def __init__(self):
                self.counter = 0

        def create_handler(event, counter):
            def handler(id):
                counter.counter += 1
                jobinfo.update_status('processing row %s' % counter.counter)
                outwriter.writerow([';'.join(id) if id else '', event])
            return handler

        counter = Counter()
        handlers = dict(
            (e, create_handler(e, counter)) for e in SpreadsheetImport.events)

        fieldset = FieldSet.objects.filter(
            id=arg['fieldset']) if arg['fieldset'] else None

        collections = Collection.objects.filter(id__in=arg['collections'])

        imp = SpreadsheetImport(
            infile,
            collections,
            separator=arg['separator'],
            owner=jobinfo.owner if arg['personal'] else None,
            preferred_fieldset=fieldset[0] if fieldset else None,
            mapping=arg['mapping'],
            separate_fields=arg['separate_fields'],
            labels=arg['labels'],
            order=arg['order'],
            hidden=arg['hidden'],
            **handlers
        )

        logging.debug('csvimport calling run() for %s' % job)

        imp.run(arg['update'],
                arg['add'],
                arg['test'],
                collections,
                skip_rows=skip_rows)

        logging.info('csvimport complete: %s' % job)

        jobinfo.complete('Complete', '%s rows processed' % counter.counter)

    except Exception, ex:

        logging.exception('csvimport failed: %s' % job)

        jobinfo.complete('Failed: %s' % ex, None)
