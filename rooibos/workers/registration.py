from django.conf import settings
import django.db
import pika
import traceback
import logging
from collections import namedtuple


logger = logging.getLogger(__name__)

QUEUE_VERSION = '5'


workers = dict()


def register_worker(id):
    def register(worker):

        def wrapped_worker(*args, **kwargs):
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
    if '_discovered' not in workers:
        for app in settings.INSTALLED_APPS:
            try:
                __import__(app + ".workers")
                logging.debug('Imported workers for %s' % app)
            except ImportError:
                logging.debug('No workers found for %s' % app)
        workers['_discovered'] = True


Job = namedtuple('Job', 'arg')


def execute_handler(handler, arg):
    try:
        handler(arg)
        return True
    except Exception:
        logger.exception("Exception in job execution")
        return False


def worker_callback(ch, method, properties, body):
    logger.debug('worker_callback running')
    django.db.connection.ensure_connection()
    if not django.db.connection.is_usable():
        logger.error('Database connection is not usable, reconnecting')
        django.db.connection.connect()
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
        result = execute_handler(handler, job)
        logger.debug('Job %s %s completed with result %s' %
                     (job, identifier, result))
    except ValueError:
        # New mode with all data included in call
        result = execute_handler(handler, data)


def run_worker(worker, arg, **kwargs):

    options = getattr(settings, 'RABBITMQ_OPTIONS', None)
    if not options:
        logger.warn(
            'Not running worker %s, RABBITMQ_OPTIONS not defined' % worker)
        return

    discover_workers()
    logger.debug("Running worker %s with arg %s" % (worker, arg))

    connection = pika.BlockingConnection(pika.ConnectionParameters(**options))
    channel = connection.channel()
    channel.confirm_delivery()
    queue_name = 'rooibos-%s-jobs-%s' % (
        getattr(settings, 'INSTANCE_NAME', 'default'),
        QUEUE_VERSION,
    )
    # for simplicity, use queue name for routing key as well
    routing_key = queue_name
    channel.queue_declare(queue=queue_name, durable=True)
    logger.debug('Sending message to worker process')
    try:
        channel.basic_publish(
            exchange='rooibos-workers',
            routing_key=routing_key,
            body='%s %s' % (worker, arg),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
    except Exception:
        logger.exception('Could not publish message %s %s' % (worker, arg))
    finally:
        connection.close()
