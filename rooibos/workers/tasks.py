from __future__ import absolute_import, unicode_literals
import time
from ..celeryapp import owned_task


@owned_task(removeuserarg=True)
def testjob(self):
    for i in range(10):
        if not self.request.called_directly:
            self.update_state(
                state='PROGRESS',
                meta={
                    'percent': i * 10,
                }
            )
        time.sleep(1)
    return True
