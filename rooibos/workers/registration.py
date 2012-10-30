import sys
from django.conf import settings
from gearman import Task, GearmanWorker, GearmanClient
from gearman.connection import GearmanConnection
from gearman.task import Taskset

workers = dict()

client = settings.GEARMAN_SERVERS and GearmanClient(settings.GEARMAN_SERVERS) or None


def register_worker(id):
    def register(worker):
        workers[id] = worker
        return worker
    return register


def discover_workers():
    if not workers:
        for app in settings.INSTALLED_APPS:
            try:
                module = __import__(app + ".workers")
            except ImportError:
                pass


def create_worker():
    discover_workers()
    worker = GearmanWorker(settings.GEARMAN_SERVERS)
    for id, func in workers.iteritems():
        worker.register_function(id, func)
    return worker


def run_worker(worker, arg, **kwargs):
    discover_workers()
    task = Task(worker, arg, **kwargs)
    if client:
        if task.background:
            taskset = Taskset([task])
            try:
                client.do_taskset(taskset)
            except GearmanConnection.ConnectionError:
                # try again, perhaps server connection was reset
                client.do_taskset(taskset)
            return task.handle
        else:
            return client.do_task(task)
    else:
        if workers.has_key(worker):
            return workers[worker](task)
        else:
            raise NotImplementedError()
