import sys
from django.conf import settings
from django.db import connection
from gearman import Task, GearmanWorker, GearmanClient
from gearman.connection import GearmanConnection
from gearman.task import Taskset

import traceback
import logging

from django.db import transaction

@transaction.commit_manually
def flush_transaction():
    """
    Flush the current transaction so we don't read stale data

    Use in long running processes to make sure fresh data is read from
    the database.  This is a problem with MySQL and the default
    transaction mode.  You can fix it by setting
    "transaction-isolation = READ-COMMITTED" in my.cnf or by calling
    this function at the appropriate moment
    """
    transaction.commit()


workers = dict()

client = settings.GEARMAN_SERVERS and GearmanClient(settings.GEARMAN_SERVERS) or None


def register_worker(id):
    def register(worker):

        def wrapped_worker(*args, **kwargs):
            flush_transaction()
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
    flush_transaction()
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
