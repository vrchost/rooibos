from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rooibos.data.models import Collection, Field
from rooibos.data.functions import collection_dump
from optparse import make_option
from django.conf import settings
from rooibos.workers.models import JobInfo
import csv
import random
import shutil
import string
import os
from rooibos.data.views import _get_scratch_dir  # TODO: make proper function
from django.utils import simplejson


class Command(BaseCommand):
    help = 'Command line metadata import tool'

    option_list = BaseCommand.option_list + (
        make_option('--mapping', '-m', dest='mapping_file',
                    help='Mapping CSV file'),
        make_option('--data', '-d', dest='data_file',
                    help='Data CSV file'),
        make_option('--collection', '-c', dest='collections',
                   action='append',
                    help='Collection identifier (multiple allowed)'),
    )


    def handle(self, *args, **kwargs):

        mapping_file = kwargs.get('mapping_file')
        data_file = kwargs.get('data_file')
        collections = map(int, kwargs.get('collections') or list())

        if not mapping_file or not data_file or not collections:
            print "--collection, --mapping and --data are required parameters"
            return

        fields = dict(
            (f.full_name, f) for f in Field.objects.all()
        )

        def get_field_id(field_name):
            f = fields.get(field_name)
            if not f:
                print "WARNING: Field %s not found" % field_name
                return None
            return f.id

        def str2bool(value):
            return value.lower() in ("1", "true", "t", "yes", "y")

        mappings = []
        with open(mapping_file, 'rU') as mapping_fileobj:
            mapping = csv.DictReader(mapping_fileobj)
            for m in mapping:
                m['mapto'] = get_field_id(m['mapto'])
                mappings.append(m)

        mapping = dict(
            (m['field'], m['mapto']) for m in mappings
        )
        separate_fields = dict(
            (m['field'], str2bool(m['separate'])) for m in mappings
        )
        labels = dict(
            (m['field'], m['label']) for m in mappings
        )
        hidden = dict(
            (m['field'], str2bool(m['hidden'])) for m in mappings
        )
        order = dict(
            (m['field'], int(m['order'])) for m in mappings
        )

        filename = "".join(random.sample(string.letters + string.digits, 32))
        full_path = os.path.join(_get_scratch_dir(), 'cmdline=' + filename)
        shutil.copy(data_file, full_path)

        JobInfo.objects.create(
            owner=User.objects.get(username='admin'),
            func='csvimport',
            arg=simplejson.dumps(dict(
                file='cmdline=' + filename,
                separator=';',
                collections=collections,
                update=True,
                add=True,
                test=False,
                personal=False,
                fieldset=None,
                mapping=mapping,
                separate_fields=separate_fields,
                labels=labels,
                order=order,
                hidden=hidden,
                )))

        print "Job submitted"
