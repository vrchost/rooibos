from __future__ import absolute_import
from celery import Celery
from functools import wraps
from kombu import Queue
from django.conf import settings
from rooibos.workers.models import TaskOwnership


app = Celery('rooibos')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

_instance_name = getattr(settings, 'INSTANCE_NAME', '')
queue_name =  'celery-%s' % (_instance_name or 'default')
solr_queue_name = queue_name + '-solr'

app.conf.task_default_queue = queue_name
app.conf.task_queues = (
    Queue(queue_name, routing_key=queue_name),
    Queue(solr_queue_name, routing_key=solr_queue_name),
)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


def owned_task(*args, **kwargs):

    def create_owned_task(userarg='owner', removeuserarg=False, **kwargs):

        def wrapper(func):
            kwargs['bind'] = True

            @app.task(**kwargs)
            @wraps(func)
            def wrapped(self, *args, **kwargs):
                if not self.request.called_directly and userarg in kwargs:
                    user = kwargs[userarg]
                    TaskOwnership.objects.get_or_create(
                        task_id=self.request.id,
                        owner_id=user,
                    )
                    if removeuserarg:
                        del kwargs[userarg]
                return func(self, *args, **kwargs)

            return wrapped

        return wrapper

    if len(args) == 1:
        if callable(args[0]):
            return create_owned_task(**kwargs)(*args)
        raise TypeError('argument 1 to @owned_task() must be a callable')
    if args:
        raise TypeError(
            '@owned_task() takes exactly 1 argument ({0} given)'.format(
                sum([len(args), len(kwargs)])))
    return create_owned_task(**kwargs)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from rooibos.solr.tasks import index
    sender.add_periodic_task(30.0, index.s(), name='solr index every 30s')
