
import os
from ..celeryapp import owned_task
from .models import Collection
from .spreadsheetimport import SpreadsheetImport


@owned_task
def csvimport(
        self, owner, filename, collection_ids,
        mapping, labels, order, hidden, refinements,
        update, add, test, personal,
        separator, separate_fields):

    from .views import _get_scratch_dir
    file = os.path.join(_get_scratch_dir(), filename)

    infile = open(file, 'rU')

    class Counter(object):
        def __init__(self):
            self.counter = 0

    count = dict(value=0)
    event_count = dict()

    def create_handler(event):
        def handler(*args, **kwargs):
            count['value'] += 1
            event_count[event] = event_count.get(event, 0) + 1
            self.update_state(
                state='PROGRESS',
                meta={
                    'count': count['value'],
                }
            )
        return handler

    handlers = dict(
        (e, create_handler(e))
        for e in SpreadsheetImport.events
    )

    collections = Collection.objects.filter(id__in=collection_ids)

    imp = SpreadsheetImport(
        infile,
        collections,
        separator=separator,
        owner=owner if personal else None,
        preferred_fieldset=None,
        mapping=mapping,
        separate_fields=separate_fields,
        labels=labels,
        order=order,
        hidden=hidden,
        refinements=refinements,
        **handlers
    )

    imp.run(
        update,
        add,
        test,
        collections,
    )

    return {
        'count': count['value'],
        'events': event_count,
    }
