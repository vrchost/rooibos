
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser, User
from rooibos.data.models import Collection, CollectionItem, Record, Field, \
    FieldValue
from rooibos.storage.models import Media, Storage
from rooibos.presentation.models import Presentation, PresentationItem
from rooibos.access.models import AccessControl
from .functions import PowerPointGenerator
import os
import tempfile
import logging


class PowerpointTestCase(TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.storage = Storage.objects.create(
            title='PPTXTest',
            name='pptxtest',
            system='local',
            base=self.tempdir
        )
        AccessControl.objects.create(content_object=self.storage, read=True)
        logging.getLogger().setLevel(logging.DEBUG)

    def tearDown(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        self.storage.delete()

    def test_simple_powerpoint_file(self):
        self._generate()

    def _generate(self):
        file = os.path.join(self.tempdir, 'test-presentation.pptx')
        collection = Collection.objects.create(
            title='Simple Collection', description='Simple collection')
        AccessControl.objects.create(content_object=collection, read=True)
        field = Field.objects.get(name='title', standard__prefix='dc')
        creator_field = Field.objects.get(
            name='creator', standard__prefix='dc')
        source_field = Field.objects.get(name='source', standard__prefix='dc')
        presentation = Presentation.objects.create(
            title='Simple Presentation',
            description='This is a PowerPoint presentation created from a '
            'template and populated with data.',
            owner=User.objects.get_or_create(username='admin')[0]
        )
        for n in range(1, 11):
            record = Record.objects.create()
            FieldValue.objects.create(
                record=record, field=field, value='Record %s' % n)
            FieldValue.objects.create(
                record=record,
                field=creator_field,
                value='RecordCreator %s' % n
            )
            FieldValue.objects.create(
                record=record, field=source_field, value='RecordSource %s' % n)

            CollectionItem.objects.create(collection=collection, record=record)
            PresentationItem.objects.create(
                presentation=presentation, record=record, order=n)
            media = Media.objects.create(
                record=record, storage=self.storage, mimetype='image/jpeg')
            with open(os.path.join(
                    os.path.dirname(__file__),
                    'test_data', '%02d.jpg' % n), 'rb') as f:
                media.save_file('%02d.jpg' % n, f)

        g = PowerPointGenerator(presentation, AnonymousUser())

        self.assertTrue(g.generate(file, 'white', True, True))
        self.assertTrue(g.generate(file, 'white', True, False))
        self.assertTrue(g.generate(file, 'white', False, False))
