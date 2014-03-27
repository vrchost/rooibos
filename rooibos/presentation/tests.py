from __future__ import with_statement
import unittest
import tempfile
import os.path
import Image
import shutil
from StringIO import StringIO
from rooibos.data.models import Collection, CollectionItem, Record
from rooibos.storage.models import Media, Storage
from rooibos.access.models import AccessControl, User
from rooibos.presentation.models import Presentation, PresentationItem
from viewers import PackageFilesViewer
from zipfile import ZipFile


class PackagePresentationTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(
            title='Test', name='test', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='monalisa')
        CollectionItem.objects.create(
            collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, read=True)
        AccessControl.objects.create(content_object=self.collection, read=True)

    def tearDown(self):
        self.record.delete()
        self.storage.delete()
        self.collection.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def testSizeAccess(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(
            record=self.record, name='tiff', mimetype='image/tiff',
            storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), '..', 'storage',
                               'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        user1 = User.objects.create(username='test1890235352355')
        user2 = User.objects.create(username='test2085645642359')
        user3 = User.objects.create(username='test0382365867399')

        AccessControl.objects.create(
            content_object=self.collection, user=user1, read=True)
        AccessControl.objects.create(
            content_object=self.collection, user=user2, read=True)

        AccessControl.objects.create(
            content_object=self.storage, user=user1, read=True)
        AccessControl.objects.create(
            content_object=self.storage, user=user2, read=True,
            restrictions=dict(width=200, height=200))

        p = Presentation.objects.create(title='PackageTest', owner=user3)
        AccessControl.objects.create(content_object=p, user=user1, read=True)
        AccessControl.objects.create(content_object=p, user=user2, read=True)

        PresentationItem.objects.create(
            presentation=p, record=self.record, order=1)

        viewer1 = PackageFilesViewer(p, user1)
        viewer2 = PackageFilesViewer(p, user2)

        class FakeRequest(object):
            def __init__(self, user):
                self.user = user
                self.session = dict()

        response1 = viewer1.view(FakeRequest(user1))
        response2 = viewer2.view(FakeRequest(user1))

        image1 = StringIO(
            ZipFile(StringIO(response1)).read('0001 Slide 1.jpg'))
        image2 = StringIO(
            ZipFile(StringIO(response2)).read('0001 Slide 1.jpg'))

        width1, height1 = Image.open(image1).size
        width2, height2 = Image.open(image2).size

        self.assertEqual(615, width1)
        self.assertEqual(461, height1)
        self.assertEqual(200, width2)
        self.assertEqual(149, height2)
