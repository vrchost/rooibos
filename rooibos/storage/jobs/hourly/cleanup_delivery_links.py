from django_extensions.management.jobs import HourlyJob
from rooibos.storage.models import Storage
from time import time
import os


class Job(HourlyJob):
    help = "Clean up delivery links"

    def execute(self):

        # get current time
        valid = hex(int(time()))[2:]  # cut off 0x prefix

        for storage in Storage.objects.filter(deliverybase__gt=''):
            for file in os.listdir(storage.deliverybase):
                parts = file.split('-', 2)
                if len(parts) == 3 and len(parts[1]) == 16 and \
                        parts[0] < valid:
                    try:
                        os.remove(os.path.join(storage.deliverybase, file))
                    except OSError:
                        pass
