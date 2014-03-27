from django.conf import settings
import pika
import traceback
import logging
from collections import namedtuple
from django.db import transaction


logger = logging.getLogger('rooibos_workers_registration')


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


def register_worker(id):
    def register(worker):

        def wrapped_worker(*args, **kwargs):
            flush_transaction()
            try:
                return worker(*args, **kwargs)
            except:
                logger.exception(traceback.format_exc())
                raise

        workers[id] = wrapped_worker
        logger.debug('Registered worker %s' % id)
        return workers[id]
    return register


def discover_workers():
    if not '_discovered' in workers:
        for app in settings.INSTALLED_APPS:
            try:
                __import__(app + ".workers")
                logging.debug('Imported workers for %s' % app)
            except ImportError:
                logging.debug('No workers found for %s' % app)
        workers['_discovered'] = True


Job = namedtuple('Job', 'arg')


def worker_callback(ch, method, properties, body):
    logger.debug('worker_callback running')
    discover_workers()
    jobname, data = body.split()
    handler = workers.get(jobname)
    if not handler:
        logger.error('Received job with unknown method %s. '
                      'Known workers are %s' % (jobname, workers.keys()))
        return
    logger.debug('Running job %s %s' % (jobname, data))
    try:
        # Classic mode with Job record identifier
        identifier = int(data)
        job = Job(arg=identifier)  # for backwards compatibility
        handler(job)
        logger.debug('Job %s %s completed' % (job, identifier))
    except ValueError:
        # New mode with all data included in call
        handler(data)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def run_worker(worker, arg, **kwargs):
    flush_transaction()
    discover_workers()
    logger.debug("Running worker %s with arg %s" % (worker, arg))

    connection = pika.BlockingConnection(pika.ConnectionParameters(
        **getattr(settings, 'RABBITMQ_OPTIONS', dict(host='localhost'))))
    channel = connection.channel()

    queue_name = 'rooibos-%s-jobs' % (
        getattr(settings, 'INSTANCE_NAME', 'default'))
    channel.queue_declare(queue=queue_name, durable=True)
    logger.debug('Sending message to worker process')
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body='%s %s' % (worker, arg),
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # make message persistent
                          ))
    connection.close()
