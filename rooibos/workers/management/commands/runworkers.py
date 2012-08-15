import os
from threading import Thread
from django.core.management.base import BaseCommand
from django.conf import settings
from rooibos.workers.registration import create_worker
from rooibos.workers.models import JobInfo
from gearman.server import GearmanServer
from optparse import make_option
import rooibos.contrib.djangologging.middleware # does not get loaded otherwise
import logging


class Server(Thread):

    def __init__(self, verbosity):
        super(Server, self).__init__()
        self.verbosity = verbosity

    def run(self):
        if self.verbosity > 0:
            logging.info("Starting server")
        self.server = GearmanServer(settings.GEARMAN_SERVERS[0])
        self.server.start()


class Command(BaseCommand):
    help = 'Starts Gearman compatible workers'

    option_list = BaseCommand.option_list + (
        make_option('--server', action='store_true',
            help='Run a simple Gearman compatible server'),
        )

    def handle(self, *commands, **options):

        verbosity = options.get('verbosity', 1)
        server = options.get('server', False)

        if not settings.GEARMAN_SERVERS:
            logging.error("No gearman servers configured")
            return

        if server:
            Server(verbosity).start()

            # Restart incomplete jobs
            for job in JobInfo.objects.filter(completed=False):
                job.run()

        worker = create_worker()
        if verbosity > 0:
            logging.info("Starting workers: " + ', '.join(worker.abilities.keys()))
        worker.work()
