from django.core.management.base import BaseCommand
from ...spreadsheetimport import submit_import_job
import random
import shutil
import string
import os
from ...views import _get_scratch_dir


class Command(BaseCommand):
    help = 'Command line metadata import tool'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mapping', '-m', dest='mapping_file',
            help='Mapping CSV file'
        )
        parser.add_argument(
            '--data', '-d', dest='data_file',
            help='Data CSV file'
        )
        parser.add_argument(
            '--collection', '-c', dest='collections',
            action='append',
            help='Collection identifier (multiple allowed)'
        )

    def handle(self, *args, **kwargs):

        mapping_file = kwargs.get('mapping_file')
        data_file = kwargs.get('data_file')
        collections = list(map(int, kwargs.get('collections') or list()))

        if not mapping_file or not data_file or not collections:
            print("--collection, --mapping and --data are required parameters")
            return

        filename = "".join(random.sample(string.ascii_lowercase + string.digits, 32))
        filename = 'cmdline=' + filename
        full_path = os.path.join(_get_scratch_dir(), filename)
        shutil.copy(data_file, full_path)


        task = submit_import_job(mapping_file, filename, collections)

        print("Job submitted: %s" % task.id)
