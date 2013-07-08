import sys
from django.conf import settings
from django.db import connection
from gearman import Task, GearmanWorker, GearmanClient
from gearman.connection import GearmanConnection
from gearman.task import Taskset

import traceback
import logging

workers = dict()

client = settings.GEARMAN_SERVERS and GearmanClient(settings.GEARMAN_SERVERS) or None


def register_worker(id):
    def register(worker):

        def wrapped_worker(*args, **kwargs):
            logging.debug('Closing DB connection to force reconnect for job %s' % id)
            connection.close()
            try:
                return worker(*args, **kwargs)
            except:
                logging.exception(traceback.format_exc())
                raise

        workers[id] = wrapped_worker
        return workers[id]
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
    logging.debug("Running worker %s with arg %s" % (worker, arg))
    task = Task(worker, arg, **kwargs)
    if client:
        logging.debug("Using gearman")
        if task.background:
            logging.debug("Running task in background")
            taskset = Taskset([task])
            try:
                client.do_taskset(taskset)
            except GearmanConnection.ConnectionError:
                logging.debug("ConnectionError, trying once more")
                # try again, perhaps server connection was reset
                client.do_taskset(taskset)
            logging.debug("Done scheduling background task")
            return task.handle
        else:
            logging.debug("Running task immediately")
            return client.do_task(task)
    else:
        logging.debug("Gearman not found, running immediately")
        if workers.has_key(worker):
            return workers[worker](task)
        else:
            raise NotImplementedError()
