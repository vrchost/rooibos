from __future__ import absolute_import, unicode_literals
from ..celeryapp import app
from .models import TaskOwnership
from django.contrib.auth.models import User
import time


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


@owned_task
def testjob(self, owner=None):
    for i in range(10):
        if not self.request.called_directly:
            self.update_state(
                state='PROGRESS',
                meta={
                    'percent': i * 10,
                }
            )
        time.sleep(1)
