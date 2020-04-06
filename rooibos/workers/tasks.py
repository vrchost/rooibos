
import os
import time
from datetime import datetime
from django.conf import settings
from ..celeryapp import owned_task


def _get_scratch_dir():
    path = os.path.join(settings.SCRATCH_DIR, 'job-attachment')
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_attachment(self):
    name = '%s-%s.txt' % (self.name.split('.')[-1], self.request.id)
    path = os.path.join(_get_scratch_dir(), name)
    return path


@owned_task(removeuserarg=True)
def testjob(self):
    results = []
    for i in range(10):
        if not self.request.called_directly:
            self.update_state(
                state='PROGRESS',
                meta={
                    'percent': i * 10,
                }
            )
            results.append('Completed %d%% at %s\n' % (i * 10, datetime.now()))
        time.sleep(1)
    attachment = get_attachment(self)
    with open(attachment, 'w') as attachment_file:
        attachment_file.writelines(results)
    return {
        'attachment': attachment,
    }
