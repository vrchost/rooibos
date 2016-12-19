from __future__ import absolute_import, unicode_literals
from celery import Celery
from django.contrib.auth.models import User
from rooibos.workers.models import TaskOwnership


app = Celery('rooibos')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

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
            def wrapped(self, *args, **kwargs):
                if not self.request.called_directly and userarg in kwargs:
                    user = kwargs[userarg]
                    if not isinstance(user, User):
                        user = User.objects.get(username=user)
                    TaskOwnership.objects.get_or_create(
                        task_id=self.request.id,
                        owner=user,
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
