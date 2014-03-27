from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
import time


@register_worker('testjob')
def testjob(job):
    jobinfo = JobInfo.objects.get(id=job.arg)
    arguments = jobinfo.arg
    if arguments != 'This is a test':
        jobinfo.complete('Failed', 'Received incorrect argument')
    else:
        for i in range(10):
            jobinfo.update_status("%d%% complete" % (i * 10))
            time.sleep(1)
        jobinfo.complete('Complete', 'Test job complete')
