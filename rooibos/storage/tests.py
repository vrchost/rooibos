from __future__ import with_statement
import unittest
import tempfile
import os.path
import Image
import shutil
from threading import Thread
from StringIO import StringIO
from django.test.client import Client
from django.core.files import File
from django.utils import simplejson
from django.conf import settings
from rooibos.data.models import *
from rooibos.storage.models import Media, ProxyUrl, Storage, TrustedSubnet
from localfs import LocalFileSystemStorageSystem
from rooibos.storage import get_thumbnail_for_record, get_media_for_record, get_image_for_record, match_up_media, analyze_records, analyze_media
from rooibos.access.models import AccessControl
from rooibos.access import get_effective_permissions
from rooibos.presentation.models import Presentation, PresentationItem
from sqlite3 import OperationalError


class LocalFileSystemStorageSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test', name='test', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='monalisa')
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, read=True)
        AccessControl.objects.create(content_object=self.collection, read=True)

    def tearDown(self):
        self.record.delete()
        self.storage.delete()
        self.collection.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_save_and_retrieve_file(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='image', storage=self.storage)
        content = StringIO('hello world')
        media.save_file('test.txt', content)

        self.assertEqual('test.txt', media.url)

        content = media.load_file()
        self.assertEqual('hello world', content.read())

        media.delete()

    def test_save_over_existing_file(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='image', storage=self.storage)
        content = StringIO('hello world')
        media.save_file('test.txt', content)

        media2 = Media.objects.create(record=self.record, name='image', storage=self.storage)

        content2 = StringIO('hallo welt')
        media2.save_file('test.txt', content2)
        self.assertNotEqual('test.txt', media2.url)
        self.assertNotEqual('test', media2.name)

        self.assertEqual('hello world', media.load_file().read())
        self.assertEqual('hallo welt', media2.load_file().read())


    def test_thumbnail(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        thumbnail = get_thumbnail_for_record(self.record)
        width, height = Image.open(thumbnail).size
        self.assertTrue(width == 100)
        self.assertTrue(height < 100)

        media.delete()


    def test_crop_to_square(self):

        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        thumbnail = get_thumbnail_for_record(self.record, crop_to_square=True)
        width, height = Image.open(thumbnail).size
        self.assertTrue(width == 100)
        self.assertTrue(height == 100)

        media.delete()


    def test_derivative_permissions(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        user1 = User.objects.create(username='test1890723589075')
        user2 = User.objects.create(username='test2087358972359')

        AccessControl.objects.create(content_object=self.collection, user=user1, read=True)
        AccessControl.objects.create(content_object=self.collection, user=user2, read=True)

        AccessControl.objects.create(content_object=self.storage, user=user1, read=True)
        AccessControl.objects.create(content_object=self.storage, user=user2, read=True,
                                     restrictions=dict(width=200, height=200))

        result1 = get_image_for_record(self.record, width=400, height=400, user=user1)
        result2 = get_image_for_record(self.record, width=400, height=400, user=user2)

        self.assertEqual(400, Image.open(result1).size[0])
        self.assertEqual(200, Image.open(result2).size[0])

        result3 = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(result2, result3)

        media.delete()


    def test_access_through_presentation(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        user1 = User.objects.create(username='test3097589074404')
        user2 = User.objects.create(username='test4589570974047')

        AccessControl.objects.create(content_object=self.collection, user=user1, read=True)
        storage_acl = AccessControl.objects.create(content_object=self.storage, user=user1, read=True)

        presentation = Presentation.objects.create(title='test47949074', owner=user1)
        presentation.items.create(record=self.record, order=1)

        # user2 has no access to storage or collection, so should not get result
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(None, result)

        # give access to presentation
        AccessControl.objects.create(content_object=presentation, user=user2, read=True)

        # user2 has no access to storage yet, so still should not get result
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(None, result)

        # give user2 access to storage
        user2_storage_acl = AccessControl.objects.create(content_object=self.storage, user=user2, read=True)

        # now user2 should get the image
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(400, Image.open(result).size[0])

        # limit user2 image size
        user2_storage_acl.restrictions = dict(width=200, height=200)
        user2_storage_acl.save()

        # we should now get a smaller image
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(200, Image.open(result).size[0])

        # password protect the presentation
        presentation.password='secret'
        presentation.save()

        # user2 has not provided presentation password, so should not get result
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(None, result)

        # with presentation password, image should be returned
        result = get_image_for_record(self.record, width=400, height=400, user=user2,
                                      passwords={presentation.id: 'secret'})
        self.assertEqual(200, Image.open(result).size[0])


    def testDeliveryUrl(self):
        s = Storage.objects.create(title='TestDelivery',
                                   system='local',
                                   base='t:/streaming/directory',
                                   urlbase='rtmp://streaming:80/videos/mp4:test/%(filename)s')

        media = Media.objects.create(record=self.record,
                                     name='tiff',
                                     mimetype='video/mp4',
                                     storage=s,
                                     url='test.mp4')

        self.assertEqual('rtmp://streaming:80/videos/mp4:test/test.mp4', media.get_delivery_url())


class ImageCompareTest(unittest.TestCase):

    def test_compare(self):
        from rooibos.storage import _imgsizecmp

        class image:
            def __init__(self, w, h):
                self.width = w
                self.height = h

        data = [image(w, h) for w in (10, None, 20) for h in (15, 5, None)]

        data = sorted(data, _imgsizecmp)[::-1]


        self.assertEqual(data[0].width, 20)
        self.assertEqual(data[0].height, 15)

        self.assertEqual(data[1].width, 10)
        self.assertEqual(data[1].height, 15)

        self.assertEqual(data[2].width, 20)
        self.assertEqual(data[2].height, 5)

        self.assertEqual(data[3].width, 10)
        self.assertEqual(data[3].height, 5)


class ProxyUrlTest(unittest.TestCase):

    def setUp(self):
        self.user = User.objects.create(username='proxytest')
        self.user.set_password('test')
        self.user.save()
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test', name='test', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='monalisa')
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, user=self.user, read=True,
                                     restrictions=dict(width=50, height=50))
        AccessControl.objects.create(content_object=self.collection, user=self.user, read=True)
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

    def tearDown(self):
        self.record.delete()
        self.storage.delete()
        self.collection.delete()
        self.user.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_proxy_url(self):

        c = Client()
        response = c.post('/media/proxy/create/')
        # Response is JSON, should always be 200
        self.assertEqual(200, response.status_code)
        # Result should be error since we did not provide any credentials
        data = simplejson.loads(response.content)
        self.assertEqual('error', data['result'])

        login = c.login(username='proxytest', password='test')
        self.assertTrue(login)

        TrustedSubnet.objects.create(subnet='127.0.0.1')

        response = c.post('/media/proxy/create/',
                          {'url': self.record.get_thumbnail_url(), 'context': '_1_2'},
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        data = simplejson.loads(response.content)
        self.assertEqual('ok', data['result'])
        id = data['id']
        c.logout()

        # try to retrieve content
        url = '/media/proxy/%s/' % id
        response = c.get(url, {'context': '_1_2'})
        self.assertEqual(200, response.status_code)
        self.assertEqual('image/jpeg', response['content-type'])

        # make sure image dimension restrictions took effect
        image = Image.open(StringIO(response.content))
        width, height = image.size
        self.assertEqual(50, width)


    def test_duplicate_proxy_url(self):

        TrustedSubnet.objects.create(subnet='127.0.0.1')
        proxy_url = ProxyUrl.create_proxy_url('/some/url', 'ctx1', '127.0.0.1', self.user)
        proxy_url2 = ProxyUrl.create_proxy_url('/some/url', 'ctx2', '127.0.0.1', self.user)
        proxy_url3 = ProxyUrl.create_proxy_url('/some/url', 'ctx1', '127.0.0.1', self.user)
        self.assertEqual(proxy_url.uuid, proxy_url3.uuid)
        self.assertNotEqual(proxy_url.uuid, proxy_url2.uuid)


class OnlineStorageSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test', name='test', system='online')
        self.record = Record.objects.create(name='monalisa')
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, read=True)
        AccessControl.objects.create(content_object=self.collection, read=True)

    def tearDown(self):
        self.record.delete()
        self.storage.delete()
        self.collection.delete()

    def test_retrieval(self):
        url = "file:///" + os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif').replace('\\', '/')
        media = Media.objects.create(record=self.record, storage=self.storage, url=url, mimetype='image/tiff')
        thumbnail = get_thumbnail_for_record(self.record)
        width, height = Image.open(thumbnail).size
        self.assertTrue(width == 100)
        self.assertTrue(height < 100)

        media.delete()


class PseudoStreamingStorageSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test',
                                              name='test',
                                              system='pseudostreaming',
                                              base=self.tempdir,
                                              urlbase='file:///' + self.tempdir.replace('\\', '/'))
        self.record = Record.objects.create(name='record')
        self.media = Media.objects.create(record=self.record, name='image', storage=self.storage)
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, read=True)
        AccessControl.objects.create(content_object=self.collection, read=True)

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)
        self.record.delete()
        self.storage.delete()
        self.collection.delete()

    def test_pseudostreaming(self):
        TEST_STRING = 'Hello world'
        content = StringIO(TEST_STRING)
        self.media.save_file('test.txt', content)
        c = Client()
        response = c.get(self.media.get_absolute_url())
        self.assertEqual(TEST_STRING, response.content)


class ProtectedContentDownloadTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='ProtectedTest')
        self.storage = Storage.objects.create(title='ProtectedTest', name='protectedtest', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='protected')
        self.user = User.objects.create_user('protectedtest', 'test@example.com', 'test')
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, user=self.user, read=True)
        AccessControl.objects.create(content_object=self.collection, user=self.user, read=True)
        Media.objects.filter(record=self.record).delete()
        self.media = Media.objects.create(record=self.record, name='protectedimage', storage=self.storage)
        content = StringIO('hello world')
        self.media.save_file('test.txt', content)

    def tearDown(self):
        self.media.delete()
        self.record.delete()
        self.storage.delete()
        self.collection.delete()
        self.user.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_save_and_retrieve_file(self):

        if not any(map(lambda c: c.endswith('.auth.middleware.BasicAuthenticationMiddleware'), settings.MIDDLEWARE_CLASSES)):
            return

        c = Client()
        # not logged in
        response = c.get(self.media.get_absolute_url())
        self.assertEqual(401, response.status_code)

        # with basic auth
        response = c.get(self.media.get_absolute_url(),
                         HTTP_AUTHORIZATION='basic %s' % 'protectedtest:test'.encode('base64').strip())
        self.assertEqual(200, response.status_code)
        self.assertEqual('hello world', response.content)

        # now logged in
        response = c.get(self.media.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertEqual('hello world', response.content)


class AutoConnectMediaTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.tempdir, 'sub'))
        self.collection = Collection.objects.create(title='AutoconnectMediaTest')
        self.storage = Storage.objects.create(title='AutoconnectMediaTest', system='local', base=self.tempdir)
        self.records = []
        self.create_file('id_1')
        self.create_file('id_2')
        self.create_file(os.path.join('sub', 'id_99'))

    def tearDown(self):
        for record in self.records:
            record.delete()
        self.storage.delete()
        self.collection.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def create_record(self, id):
        record = Record.objects.create(name='id')
        CollectionItem.objects.create(collection=self.collection, record=record)
        FieldValue.objects.create(record=record, field=standardfield('identifier'), value=id)
        self.records.append(record)
        return record

    def create_file(self, id):
        file = open(os.path.join(self.tempdir, '%s.txt' % id), 'w')
        file.write('test')
        file.close()

    def test_get_files(self):
        files = sorted(self.storage.get_files())
        self.assertEqual(3, len(files))
        self.assertEqual('id_1.txt', files[0])
        self.assertEqual('id_2.txt', files[1])
        self.assertEqual(os.path.join('sub', 'id_99.txt'), files[2])

    def test_get_files_in_subdirectories(self):
        pass

    def test_connect_files(self):
        r1 = self.create_record('id_1')
        r2 = self.create_record('id_2')
        r3 = self.create_record('id_3')
        Media.objects.create(record=r1, storage=self.storage, url='id_1.txt')

        matches = list(match_up_media(self.storage, self.collection))

        self.assertEqual(1, len(matches))
        match = matches[0]
        record, file_url = match
        self.assertEqual(r2, record)
        self.assertEqual('id_2.txt', file_url)


class AnalyzeTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.tempdir, 'sub'))
        self.collection = Collection.objects.create(title='AnalyzeTest')
        self.storage = Storage.objects.create(title='AnalyzeTest', system='local', base=self.tempdir)
        self.other_storage = Storage.objects.create(title='OtherAnalyzeTest', system='local', base=self.tempdir)
        self.records = []
        self.create_file('id_1')
        self.create_file('id_2')
        self.create_file(os.path.join('sub', 'id_99'))
        self.create_record('id_1', 'id_1')
        self.create_record('id_missing', 'id_missing')
        self.create_record('id_no_media', None)
        self.create_record('id_missing_other', 'id_missing_other', self.other_storage)

    def tearDown(self):
        for record in self.records:
            record.delete()
        self.storage.delete()
        self.collection.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def create_record(self, id, media, storage=None):
        record = Record.objects.create(name='id')
        CollectionItem.objects.create(collection=self.collection, record=record)
        FieldValue.objects.create(record=record, field=standardfield('identifier'), value=id)
        FieldValue.objects.create(record=record, field=standardfield('title'), value=id)
        self.records.append(record)
        if media:
            record.media_set.create(storage=storage or self.storage, url='%s.txt' % media)
        return record

    def create_file(self, id):
        file = open(os.path.join(self.tempdir, '%s.txt' % id), 'w')
        file.write('test')
        file.close()

    def testAnalyzeCollection(self):

        empty = analyze_records(self.collection, self.storage)

        self.assertEqual(2, len(empty))
        titles = sorted(e.title for e in empty)
        self.assertEqual('id_missing_other', titles[0])
        self.assertEqual('id_no_media', titles[1])

    def testAnalyzeMedia(self):

        broken, extra = analyze_media(self.storage)

        self.assertEqual(1, len(broken))
        self.assertEqual('id_missing.txt', broken[0].url)

        self.assertEqual(2, len(extra))
        extra = sorted(extra)
        self.assertEqual('id_2.txt', extra[0])
        self.assertEqual(os.path.join('sub', 'id_99.txt'), extra[1])



class GetMediaForRecordTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='GetMediaTest')
        self.storage = Storage.objects.create(title='GetMediaTest', name='getmediatest', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='monalisa')
        self.record.media_set.create(name='getmediatest', url='getmediatest', storage=self.storage)
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        self.user = User.objects.create(username='getmediatest1')
        self.owner_can_read = User.objects.create(username='getmediatest2')
        self.owner_cant_read = User.objects.create(username='getmediatest3')
        AccessControl.objects.create(user=self.owner_can_read, content_object=self.collection, read=True)
        self.record_standalone = Record.objects.create(name='no_collection', owner=self.owner_can_read)
        self.record_standalone.media_set.create(name='getmediatest', url='getmediatest', storage=self.storage)
        self.presentation_ok = Presentation.objects.create(title='GetMediaTest1', owner=self.owner_can_read)
        self.presentation_ok.items.create(record=self.record, order=1)
        self.presentation_hidden = Presentation.objects.create(title='GetMediaTest5', owner=self.owner_can_read, hidden=True)
        self.presentation_hidden.items.create(record=self.record, order=1)
        self.presentation_broken = Presentation.objects.create(title='GetMediaTest2', owner=self.owner_cant_read)
        self.presentation_broken.items.create(record=self.record, order=1)
        self.presentation_password = Presentation.objects.create(title='GetMediaTest3', owner=self.owner_can_read, password='test')
        self.presentation_password.items.create(record=self.record, order=1)
        self.presentation_no_record = Presentation.objects.create(title='GetMediaTest4', owner=self.owner_can_read)
        self.presentation_standalone_record = Presentation.objects.create(title='GetMediaTest6', owner=self.owner_can_read)
        self.presentation_standalone_record.items.create(record=self.record_standalone, order=1)
        AccessControl.objects.create(user=self.user, content_object=self.storage, read=True)

    def tearDown(self):
        self.presentation_ok.delete()
        self.presentation_broken.delete()
        self.presentation_standalone_record.delete()
        self.user.delete()
        self.owner_can_read.delete()
        self.owner_cant_read.delete()
        self.record.delete()
        self.record_standalone.delete()
        self.storage.delete()
        self.collection.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_direct_access(self):
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.create(user=self.user, content_object=self.collection, read=True)
        self.assertEqual(1, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.filter(user=self.user).delete()

    def test_simple_presentation_access(self):
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.create(user=self.user, content_object=self.presentation_broken, read=True)
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.create(user=self.user, content_object=self.presentation_ok, read=True)
        self.assertEqual(1, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.filter(user=self.user).delete()

    def test_password_access(self):
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.create(user=self.user, content_object=self.presentation_password, read=True)
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        passwords = dict(((self.presentation_password.id, 'test'),))
        self.assertEqual(1, get_media_for_record(self.record, user=self.user, passwords=passwords).count())
        AccessControl.objects.filter(user=self.user).delete()

    def test_presentation_must_contain_record(self):
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.create(user=self.user, content_object=self.presentation_no_record, read=True)
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.filter(user=self.user).delete()

    def test_hidden_presentation_access(self):
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.create(user=self.user, content_object=self.presentation_hidden, read=True)
        self.assertEqual(0, get_media_for_record(self.record, user=self.user).count())
        self.presentation_hidden.hidden = False
        self.presentation_hidden.save()
        self.assertEqual(1, get_media_for_record(self.record, user=self.user).count())
        AccessControl.objects.filter(user=self.user).delete()
        self.presentation_hidden.hidden = True
        self.presentation_hidden.save()

    def test_standalone_record_access(self):
        self.assertEqual(0, get_media_for_record(self.record_standalone, user=self.user).count())
        AccessControl.objects.create(user=self.user, content_object=self.presentation_standalone_record, read=True)
        self.assertEqual(1, get_media_for_record(self.record_standalone, user=self.user).count())


class MediaNameTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.storage = Storage.objects.create(title='MediaNameTest', name='medianametest', system='local', base=self.tempdir)
        self.record = Record.objects.create()

    def tearDown(self):
        self.record.delete()
        self.storage.delete()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def testDefaultMediaName(self):
        media = self.record.media_set.create(storage=self.storage)
        self.assertTrue(media.name.startswith('m-'))

    def testMediaNameFromUrl(self):
        media = self.record.media_set.create(url='test.txt', storage=self.storage)
        self.assertEqual('test', media.name)

    def testMediaNameFromSave(self):
        media = self.record.media_set.create(storage=self.storage)
        self.assertTrue(media.name.startswith('m-'))

        content = StringIO('hello world')
        media.save_file('hello-world.txt', content)

        # check updated name
        media = self.record.media_set.filter(name='hello-world')
        self.assertEqual(1, len(media))
