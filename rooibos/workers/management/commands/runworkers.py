from django.core.management.base import BaseCommand
from django.conf import settings
from rooibos.workers.registration import worker_callback
# does not get loaded otherwise:
import rooibos.contrib.djangologging.middleware
import logging
import pika


class Command(BaseCommand):
    help = 'Starts worker process'

    option_list = BaseCommand.option_list + (
        )

    def handle(self, *commands, **options):
        logging.root.addHandler(logging.StreamHandler())

        connection = pika.BlockingConnection(pika.ConnectionParameters(
            **getattr(settings, 'RABBITMQ_OPTIONS', dict(host='localhost'))))
        channel = connection.channel()

        queue_name = 'rooibos-%s-jobs' % (
            getattr(settings, 'INSTANCE_NAME', 'default'))
        channel.queue_declare(queue=queue_name, durable=True)
        logging.debug('Started worker process, waiting for messages ' +
                      'on queue %s' % queue_name)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(worker_callback, queue=queue_name)
        channel.start_consuming()
