import unittest
from models import Collection, CollectionItem, Record, Field, FieldValue, \
    get_system_field, standardfield
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from rooibos.access.models import AccessControl
from spreadsheetimport import SpreadsheetImport
from cStringIO import StringIO


class FieldValueTestCase(unittest.TestCase):

    def setUp(self):
        self.collection = Collection.objects.create(title='Test Collection', name='test')
        self.titleField = Field.objects.create(label='Title', name='title')
        self.creatorField = Field.objects.create(label='Creator', name='creator')
        self.locationField = Field.objects.create(label='Location', name='location')
        self.user = User.objects.create(username='FieldValueTestCase-test')
        self.user2 = User.objects.create(username='FieldValueTestCase-test2')
        self.user3 = User.objects.create(username='FieldValueTestCase-test3')

    def tearDown(self):
        self.collection.delete()
        self.titleField.delete()
        self.creatorField.delete()
        self.locationField.delete()
        self.user.delete()
        self.user2.delete()
        self.user3.delete()

    def testFieldValueBasicContext(self):
        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=self.collection)

        t1 = record.fieldvalue_set.create(field=self.titleField, label='Caption', value='Photograph of Mona Lisa')
        t2 = record.fieldvalue_set.create(field=self.titleField, value='Photo Lisa')
        c1 = record.fieldvalue_set.create(field=self.creatorField, label='Photographer', value='John Doe')
        c2 = record.fieldvalue_set.create(field=self.creatorField, value='John X. Doe', context=self.collection)
        l1 = record.fieldvalue_set.create(field=self.locationField, value='Harrisonburg', owner=self.user)

        self.assertEqual(True, datetime.now() - record.created < timedelta(0, 120))
        self.assertEqual(True, datetime.now() - record.modified < timedelta(0, 120))

        self.assertEqual("Caption", t1.resolved_label)
        self.assertEqual("Title", t2.resolved_label)

        self.assertEqual(3, len(record.get_fieldvalues()))
        self.assertEqual(4, len(record.get_fieldvalues(context=self.collection)))
        self.assertEqual(4, len(record.get_fieldvalues(owner=self.user)))
        self.assertEqual(5, len(record.get_fieldvalues(owner=self.user, context=self.collection)))

    def testPresentationContext(self):
        record = Record.objects.create()
        owned_collection = Collection.objects.create(title='Owned collection', owner=self.user)

        v1 = record.fieldvalue_set.create(field=self.titleField, value='v')
        v2 = record.fieldvalue_set.create(field=self.titleField, value='v-u1', owner=self.user)
        v3 = record.fieldvalue_set.create(field=self.titleField, value='v-u2', owner=self.user2)
        v4 = record.fieldvalue_set.create(field=self.titleField, value='v-u3', owner=self.user3)
        v5 = record.fieldvalue_set.create(field=self.titleField, value='v-u1-ctx', owner=self.user, context=owned_collection)

        values = record.get_fieldvalues(owner=self.user2, context=owned_collection)
        expected = ['v', 'v-u2']
        for v in values:
            self.assertTrue(v.value in expected)
            expected.remove(v.value)
        self.assertEqual([], expected)

        values = record.get_fieldvalues(owner=self.user2, context=owned_collection, include_context_owner=True)
        expected = ['v', 'v-u1', 'v-u2', 'v-u1-ctx']
        for v in values:
            self.assertTrue(v.value in expected)
            expected.remove(v.value)
        self.assertEqual([], expected)


class GroupTestCase(unittest.TestCase):

    def testSubGroups(self):
        group_a = Collection.objects.create(title='A', name='a')
        group_b = Collection.objects.create(title='B', name='b')
        group_b1 = Collection.objects.create(title='B1', name='b1')
        group_ab = Collection.objects.create(title='AB', name='ab')

        group_b.children.add(group_b1)
        group_b.save()

        group_ab.children.add(group_a, group_b)
        group_ab.save()

        self.assertEqual(0, len(group_b1.all_child_collections))
        self.assertEqual(1, len(group_b.all_child_collections))
        self.assertEqual(0, len(group_a.all_child_collections))
        self.assertEqual(3, len(group_ab.all_child_collections))

    def testCircularSubGroups(self):
        group_c = Collection.objects.create(title='C', name='c')
        group_d = Collection.objects.create(title='D', name='d')
        group_e = Collection.objects.create(title='E', name='e')

        group_c.children.add(group_d)
        group_c.save()

        group_d.children.add(group_c)
        group_d.save()

        self.assertEqual(1, len(group_c.all_child_collections))
        self.assertEqual(1, len(group_d.all_child_collections))

        group_e.children.add(group_e)
        group_e.save()

        self.assertEqual(0, len(group_e.all_child_collections))

    def testSubGroupRecords(self):
        group_f = Collection.objects.create(title='F', name='f')
        group_g = Collection.objects.create(title='G', name='g')
        group_h = Collection.objects.create(title='H', name='h')

        group_f.children.add(group_g)
        group_f.save()

        record = Record.objects.create()
        self.assertEqual(0, len(group_f.all_records))

        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_h)
        self.assertEqual(0, len(group_f.all_records))

        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_f)
        self.assertEqual(1, len(group_f.all_records))

        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_g)
        self.assertEqual(2, len(group_f.all_records))

        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_f)
        CollectionItem.objects.create(record=record, collection=group_g)
        self.assertEqual(3, len(group_f.all_records))

    def testGetTitle(self):
        record1 = Record.objects.create()
        self.assertEqual(None, record1.title)

        dctitle = Field.objects.get(standard__prefix='dc', name='title')
        record1.fieldvalue_set.create(field=dctitle, value='The title')
        self.assertEqual('The title', record1.title)

        record2 = Record.objects.create()
        field = Field.objects.create(label='test', name='test')
        field.equivalent.add(dctitle)
        record2.fieldvalue_set.create(field=field, value='Another title')
        self.assertEqual('Another title', record2.title)



csv_file = """ID,Filename,Title,Creator,Location,Unused
A001,a001.jpg,Test,"Knab, Andreas","Harrisonburg, VA"
A002,a002.jpg,Another Test,Andreas Knab;John Doe,Virginia
"""

class CsvImportTestCase(unittest.TestCase):

    def setUp(self):
        self.collection = Collection.objects.create(title='Test Collection', name='test')
        self.titleField = Field.objects.create(label='Title', name='title')
        self.creatorField = Field.objects.create(label='Creator', name='creator')
        self.locationField = Field.objects.create(label='Location', name='location')
        self.user = User.objects.create(username='CsvImportTestCase-test')
        self.records = []

    def tearDown(self):
        for record in self.records:
            record.delete()
        self.collection.delete()
        self.titleField.delete()
        self.creatorField.delete()
        self.locationField.delete()
        self.user.delete()

    def testAnalyze(self):

        testimport = SpreadsheetImport(StringIO(csv_file), [self.collection])

        self.assertFalse(testimport.analyzed)

        data = testimport.analyze()

        self.assertTrue(testimport.analyzed)

        self.assertEqual(2, len(data))

        self.assertEqual('A001', data[0]['ID'][0])
        self.assertEqual('a001.jpg', data[0]['Filename'][0])
        self.assertEqual('Test', data[0]['Title'][0])
        self.assertEqual('Knab, Andreas', data[0]['Creator'][0])
        self.assertEqual('Harrisonburg, VA', data[0]['Location'][0])
        self.assertEqual(None, data[0]['Unused'])

        self.assertEqual('A002', data[1]['ID'][0])
        self.assertEqual('a002.jpg', data[1]['Filename'][0])
        self.assertEqual('Another Test', data[1]['Title'][0])
        self.assertEqual('Andreas Knab;John Doe', data[1]['Creator'][0])
        self.assertEqual('Virginia', data[1]['Location'][0])
        self.assertEqual(None, data[1]['Unused'])

        # These don't match anything
        self.assertEqual(None, testimport.mapping['ID'])
        self.assertEqual(None, testimport.mapping['Filename'])
        self.assertEqual(None, testimport.mapping['Unused'])

        # These should match standards fields
        self.assertNotEqual(None, testimport.mapping['Title'])
        self.assertNotEqual(None, testimport.mapping['Creator'])
        self.assertNotEqual(None, testimport.mapping['Location'])

        self.assertEqual(None, testimport.get_identifier_field())

        # Map the ID field and try again
        testimport.mapping['ID'] = Field.objects.get(name='identifier', standard__prefix='dc')
        self.assertEqual('ID', testimport.get_identifier_field())


    def testImport(self):
        testimport = SpreadsheetImport(StringIO(csv_file), [self.collection])

        self.assertFalse(testimport.analyzed)

        data = testimport.analyze()

        self.assertTrue(testimport.analyzed)


    def testFindDuplicateIdentifiers(self):
        testimport = SpreadsheetImport(StringIO(), [self.collection])

        dup = testimport.find_duplicate_identifiers()
        self.assertEqual(0, len(dup))

        dcidentifier = Field.objects.get(name='identifier', standard__prefix='dc')

        def create_record(id):
            record = Record.objects.create()
            self.records.append(record)
            record.fieldvalue_set.create(field=dcidentifier, value=id)
            CollectionItem.objects.create(record=record, collection=self.collection)

        create_record('X001')
        create_record('X002')
        create_record('X002')

        dup = testimport.find_duplicate_identifiers()
        self.assertEqual(1, len(dup))
        self.assertEqual('X002', dup[0])


    def testNoIdentifierException(self):
        testimport = SpreadsheetImport(StringIO(csv_file), [self.collection])
        self.assertRaises(SpreadsheetImport.NoIdentifierException, testimport.run)


    def testImportSimple(self):
        testimport = SpreadsheetImport(StringIO(csv_file), [self.collection])
        self.assertEqual(0, self.collection.records.count())
        testimport.analyze()

        dc = dict(
            identifier=Field.objects.get(name='identifier', standard__prefix='dc'),
            title=Field.objects.get(name='title', standard__prefix='dc'),
            creator=Field.objects.get(name='creator', standard__prefix='dc'),
            coverage=Field.objects.get(name='coverage', standard__prefix='dc'),
        )

        testimport.mapping = {
            'ID': dc['identifier'],
            'Filename': None,
            'Title': dc['title'],
            'Creator': dc['creator'],
            'Location': dc['coverage'],
        }
        testimport.name_field = 'ID'

        self.assertNotEqual(None, testimport.get_identifier_field())

        testimport.run()

        self.assertEquals(2, self.collection.records.count())

        r1 = self.collection.records.get(name='A001'.lower())
        self.assertEqual('A001', r1.fieldvalue_set.get(field=dc['identifier']).value)

    def testSplitValuesImport(self):
        testimport = SpreadsheetImport(StringIO("ID,Split,NoSplit\nA999,a;b,a;b"), [self.collection])
        testimport.analyze()
        dc = dict(
            identifier=Field.objects.get(name='identifier', standard__prefix='dc'),
            title=Field.objects.get(name='title', standard__prefix='dc'),
            creator=Field.objects.get(name='creator', standard__prefix='dc'),
        )
        testimport.mapping = {
            'ID': dc['identifier'],
            'Split': dc['title'],
            'NoSplit': dc['creator'],
        }
        testimport.name_field = 'ID'
        testimport.separate_fields = {
            'Split': True,
        }
        testimport.run()
        r = self.collection.records.get(name='A999'.lower())
        self.assertEqual('a', r.fieldvalue_set.filter(field=testimport.mapping['Split'])[0].value)
        self.assertEqual('b', r.fieldvalue_set.filter(field=testimport.mapping['Split'])[1].value)
        self.assertEqual('a;b', r.fieldvalue_set.filter(field=testimport.mapping['NoSplit'])[0].value)

    def testOwnedRecordImport(self):
        identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        title = Field.objects.get(name='title', standard__prefix='dc')
        r1 = Record.objects.create(name='x001')
        CollectionItem.objects.create(record=r1, collection=self.collection)
        r1.fieldvalue_set.create(field=identifier, value='X001')
        r1.fieldvalue_set.create(field=title, value='Standard')
        r2 = Record.objects.create(name='x002', owner=self.user)
        CollectionItem.objects.create(record=r2, collection=self.collection)
        r2.fieldvalue_set.create(field=identifier, value='X002')
        r2.fieldvalue_set.create(field=title, value='Owned')

        testimport = SpreadsheetImport(StringIO("Identifier,Title\nX001,NewTitle1\nX002,NewTitle2\nX003,NewTitle3"),
                                       [self.collection],
                                       owner=self.user)
        testimport.name_field = 'Identifier'
        testimport.run()

        self.assertEqual(1, testimport.added)
        self.assertEqual(1, testimport.updated)
        self.assertEqual(1, testimport.owner_skipped)

        r1 = self.collection.records.get(name='x001')
        r2 = self.collection.records.get(name='x002')
        r3 = self.collection.records.get(name='x003')

        self.assertEqual(None, r1.owner)
        self.assertEqual(self.user, r2.owner)
        self.assertEqual(self.user, r3.owner)

        self.assertEqual('Standard', r1.title)
        self.assertEqual('NewTitle2', r2.title)
        self.assertEqual('NewTitle3', r3.title)

    def testRecordMultiRowImport(self):
        identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        title = Field.objects.get(name='title', standard__prefix='dc')

        testimport = SpreadsheetImport(StringIO("Identifier,Title\nY001,Title1\n,Title2"),
                                       [self.collection])
        testimport.name_field = 'Identifier'
        testimport.run()

        self.assertEqual(1, testimport.added)
        self.assertEqual(0, testimport.no_id_skipped)

        r1 = self.collection.records.get(name='y001')
        titles = r1.fieldvalue_set.filter(field=title)

        self.assertEqual('Title1', titles[0].value)
        self.assertEqual('Title2', titles[1].value)

    def testRecordMultiRowImport2(self):
        identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        title = Field.objects.get(name='title', standard__prefix='dc')

        testimport = SpreadsheetImport(StringIO("""Identifier,Title
,Title1
Z001,Title2
,Title3
Z003,Title7
Z002,Title4
Z002,Title5
Z002,Title6
Z003,Title8"""),
                                       [self.collection])
        testimport.name_field = 'Identifier'
        testimport.run()

        self.assertEqual(3, testimport.added)
        self.assertEqual(0, testimport.updated)
        self.assertEqual(1, testimport.duplicate_in_file_skipped)
        self.assertEqual(1, testimport.no_id_skipped)

        t1 = self.collection.records.get(name='z001').fieldvalue_set.filter(field=title)
        t2 = self.collection.records.get(name='z002').fieldvalue_set.filter(field=title)
        t3 = self.collection.records.get(name='z003').fieldvalue_set.filter(field=title)

        self.assertEqual('Title2', t1[0].value)
        self.assertEqual('Title3', t1[1].value)

        self.assertEqual('Title4', t2[0].value)
        self.assertEqual('Title5', t2[1].value)
        self.assertEqual('Title6', t2[2].value)

        self.assertEqual('Title7', t3[0].value)

    def testSkipUpdates(self):
        identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        title = Field.objects.get(name='title', standard__prefix='dc')

        r1 = Record.objects.create(name='q001')
        CollectionItem.objects.create(record=r1, collection=self.collection)
        r1.fieldvalue_set.create(field=identifier, value='Q001')
        r1.fieldvalue_set.create(field=title, value='Title')

        testimport = SpreadsheetImport(StringIO("Identifier,Title\nQ002,NewTitle1\nQ001,NewTitle2"),
                                       [self.collection])
        testimport.name_field = 'Identifier'
        testimport.run(update=False)

        self.assertEqual(1, testimport.added)
        self.assertEqual(0, testimport.updated)
        self.assertEqual(0, testimport.added_skipped)
        self.assertEqual(1, testimport.updated_skipped)

        t1 = self.collection.records.get(name='q001').fieldvalue_set.filter(field=title)
        t2 = self.collection.records.get(name='q002').fieldvalue_set.filter(field=title)

        self.assertEqual('Title', t1[0].value)
        self.assertEqual('NewTitle1', t2[0].value)

    def testKeepSystemFieldValues(self):
        identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        title = Field.objects.get(name='title', standard__prefix='dc')
        system = get_system_field()

        r1 = Record.objects.create(name='s001')
        CollectionItem.objects.create(record=r1, collection=self.collection)
        r1.fieldvalue_set.create(field=identifier, value='S001')
        r1.fieldvalue_set.create(field=title, value='Title')
        r1.fieldvalue_set.create(field=system, value='Keep this')

        testimport = SpreadsheetImport(StringIO("Identifier,Title\nS002,NewTitle2\nS001,NewTitle1"),
                                       [self.collection])
        testimport.name_field = 'Identifier'
        testimport.run(update=True)

        self.assertEqual(1, testimport.added)
        self.assertEqual(1, testimport.updated)
        self.assertEqual(0, testimport.added_skipped)
        self.assertEqual(0, testimport.updated_skipped)

        t1 = self.collection.records.get(name='s001').fieldvalue_set.filter(field=title)
        t2 = self.collection.records.get(name='s002').fieldvalue_set.filter(field=title)
        s = self.collection.records.get(name='s001').fieldvalue_set.filter(field=system)

        self.assertEqual('NewTitle1', t1[0].value)
        self.assertEqual('NewTitle2', t2[0].value)
        self.assertEqual('Keep this', s[0].value)


    def testSkipAdds(self):
        identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        title = Field.objects.get(name='title', standard__prefix='dc')

        r1 = Record.objects.create(name='r001')
        CollectionItem.objects.create(record=r1, collection=self.collection)
        r1.fieldvalue_set.create(field=identifier, value='R001')
        r1.fieldvalue_set.create(field=title, value='Title')

        testimport = SpreadsheetImport(StringIO("Identifier,Title\nR002,NewTitle1\nR001,NewTitle2"),
                                       [self.collection])
        testimport.name_field = 'Identifier'
        testimport.run(add=False)

        self.assertEqual(0, testimport.added)
        self.assertEqual(1, testimport.updated)
        self.assertEqual(1, testimport.added_skipped)
        self.assertEqual(0, testimport.updated_skipped)

        t1 = self.collection.records.get(name='r001').fieldvalue_set.filter(field=title)
        t2 = self.collection.records.filter(name='r002')

        self.assertEqual('NewTitle2', t1[0].value)
        self.assertFalse(t2)

    def testTestOnly(self):
        identifier = Field.objects.get(name='identifier', standard__prefix='dc')
        title = Field.objects.get(name='title', standard__prefix='dc')

        r1 = Record.objects.create(name='t001')
        CollectionItem.objects.create(record=r1, collection=self.collection)
        r1.fieldvalue_set.create(field=identifier, value='T001')
        r1.fieldvalue_set.create(field=title, value='Title')

        testimport = SpreadsheetImport(StringIO("""Identifier,Title
,Title1
T001,Title2
,Title3
T003,Title7
T002,Title4
T002,Title5
T002,Title6
T003,Title8"""),
                                       [self.collection])
        testimport.name_field = 'Identifier'
        testimport.run(test=True)

        self.assertEqual(2, testimport.added)
        self.assertEqual(1, testimport.updated)
        self.assertEqual(1, testimport.duplicate_in_file_skipped)
        self.assertEqual(1, testimport.no_id_skipped)

        r = self.collection.records.filter(name__startswith='t')

        self.assertEqual(1, r.count())

        t1 = self.collection.records.get(name='t001').fieldvalue_set.filter(field=title)
        self.assertEqual('Title', t1[0].value)


    def testBOM(self):

        """Make sure the import can handle the BOM at the beginning of some UTF-8 files"""

        BOM = "\xef\xbb\xbf"
        testimport = SpreadsheetImport(StringIO(BOM + csv_file), [self.collection])
        data = testimport.analyze()

        self.assertTrue(testimport.mapping.has_key('ID'))
        self.assertTrue(testimport.mapping.has_key('Filename'))
        self.assertTrue(testimport.mapping.has_key('Unused'))
        self.assertTrue(testimport.mapping.has_key('Title'))
        self.assertTrue(testimport.mapping.has_key('Creator'))
        self.assertTrue(testimport.mapping.has_key('Location'))

    def testNoBOM(self):

        """Make sure the import can handle the lack of BOM at the beginning of some UTF-8 files"""

        testimport = SpreadsheetImport(StringIO(csv_file), [self.collection])
        data = testimport.analyze()

        self.assertTrue(testimport.mapping.has_key('ID'))
        self.assertTrue(testimport.mapping.has_key('Filename'))
        self.assertTrue(testimport.mapping.has_key('Unused'))
        self.assertTrue(testimport.mapping.has_key('Title'))
        self.assertTrue(testimport.mapping.has_key('Creator'))
        self.assertTrue(testimport.mapping.has_key('Location'))



class RecordAccessTestCase(unittest.TestCase):

    def setUp(self):
        self.collection = Collection.objects.create(title='Test Collection', name='accesstest')
        self.collection2 = Collection.objects.create(title='Test Collection', name='accesstest2')
        self.collectionreader = User.objects.create(username='accesstest-reader')
        self.collectionwriter = User.objects.create(username='accesstest-writer')
        self.collectionmanager = User.objects.create(username='accesstest-manager')
        self.owner = User.objects.create(username='accesstest-owner')
        self.admin = User.objects.get(username='admin')
        self.user = User.objects.create(username='accesstest-user')
        AccessControl.objects.create(content_object=self.collection,
                                     user=self.collectionreader,
                                     read=True)
        AccessControl.objects.create(content_object=self.collection,
                                     user=self.collectionwriter,
                                     read=True,
                                     write=True)
        AccessControl.objects.create(content_object=self.collection,
                                     user=self.collectionmanager,
                                     read=True,
                                     write=True,
                                     manage=True)
        self.records = []

    def tearDown(self):
        self.collection.delete()
        self.collection2.delete()
        self.collectionreader.delete()
        self.collectionwriter.delete()
        self.collectionmanager.delete()
        self.owner.delete()
        self.user.delete()
        for record in self.records:
            record.delete()

    def createRecord(self):
        record = Record()
        self.records.append(record)
        return record

    def checkAccess(self, record, reader, writer, manager, owner, admin, user=False):
        self.assertEqual(reader, Record.filter_by_access(self.collectionreader, record.id).count() == 1)
        self.assertEqual(writer, Record.filter_by_access(self.collectionwriter, record.id).count() == 1)
        self.assertEqual(manager, Record.filter_by_access(self.collectionmanager, record.id).count() == 1)
        self.assertEqual(owner, Record.filter_by_access(self.owner, record.id).count() == 1)
        self.assertEqual(admin, Record.filter_by_access(self.admin, record.id).count() == 1)
        self.assertEqual(user, Record.filter_by_access(self.user, record.id).count() == 1)

    def testPersonalRecordNotInCollection(self):
        record = self.createRecord()
        record.owner = self.owner
        record.save()
        self.checkAccess(record, False, False, False, True, True)

    def testPersonalRecordInCollectionNotShared(self):
        record = self.createRecord()
        record.owner = self.owner
        record.save()
        CollectionItem.objects.create(collection=self.collection, record=record, hidden=True)
        self.checkAccess(record, False, False, False, True, True)
        # Check to make sure result does not change if record is shared in another collection
        CollectionItem.objects.create(collection=self.collection2, record=record, hidden=False)
        self.checkAccess(record, False, False, False, True, True)

    def testPersonalRecordInCollectionShared(self):
        record = self.createRecord()
        record.owner = self.owner
        record.save()
        CollectionItem.objects.create(collection=self.collection, record=record, hidden=False)
        self.checkAccess(record, True, True, True, True, True)

    def testRegularRecordNotInCollection(self):
        record = self.createRecord()
        record.save()
        self.checkAccess(record, False, False, False, False, True)

    def testRegularRecordInCollectionHidden(self):
        record = self.createRecord()
        record.save()
        CollectionItem.objects.create(collection=self.collection, record=record, hidden=True)
        self.checkAccess(record, False, True, True, False, True)
        # Check to make sure result does not change if record is not hidden in another collection
        CollectionItem.objects.create(collection=self.collection2, record=record, hidden=False)
        self.checkAccess(record, False, True, True, False, True)

    def testRegularRecordInCollectionNotHidden(self):
        record = self.createRecord()
        record.save()
        CollectionItem.objects.create(collection=self.collection, record=record, hidden=False)
        self.checkAccess(record, True, True, True, False, True)


    def testIndividualRecord(self):
        record = self.createRecord()
        record.save()
        self.checkAccess(record, False, False, False, False, True, user=False)
        AccessControl.objects.create(content_object=record,
                                     user=self.user,
                                     read=True)
        self.checkAccess(record, False, False, False, False, True, user=True)

    def testIndividualEditableRecord(self):
        record = self.createRecord()
        record.save()
        # check through collection
        CollectionItem.objects.create(collection=self.collection, record=record, hidden=False)
        self.assertFalse(record.editable_by(self.collectionreader))
        self.assertTrue(record.editable_by(self.collectionwriter))
        # create ACL
        AccessControl.objects.create(content_object=record,
                                     user=self.collectionreader,
                                     read=True,
                                     write=True)
        # check again
        self.assertTrue(record.editable_by(self.collectionreader))
        self.assertFalse(record.editable_by(self.collectionwriter))


class RecordNameTestCase(unittest.TestCase):

    def setUp(self):
        self.collection = Collection.objects.create(title='Test Collection', name='test')
        self.dcid = standardfield('identifier')
        self.idfield = Field.objects.create(label='My Identifier')
        self.idfield.equivalent.add(self.dcid)

    def tearDown(self):
        self.collection.delete()
        self.idfield.delete()

    def testDefaultRecordName(self):
        record = Record.objects.create()
        self.assertTrue(record.name.startswith('r-'))

    def testRecordNameFromIdentifier(self):
        record = Record.objects.create()
        rid = record.id
        self.assertTrue(record.id)
        fv = FieldValue.objects.create(field=self.dcid,
                                       record=record,
                                       value='Identifier 205')

        record = Record.objects.get(id=rid)
        self.assertEqual('identifier-205', record.name)

        # setting field value again should not change name
        fv.save()

        record = Record.objects.get(id=rid)
        self.assertEqual('identifier-205', record.name)

    def testRecordNameFromEquivIdentifier(self):
        record = Record.objects.create()
        rid = record.id
        self.assertTrue(record.id)
        fv = FieldValue.objects.create(field=self.idfield,
                                       record=record,
                                       value='Identifier 407')

        record = Record.objects.get(id=rid)
        self.assertEqual('identifier-407', record.name)

        # setting field value again should not change name
        fv.save()

        record = Record.objects.get(id=rid)
        self.assertEqual('identifier-407', record.name)

        # make sure setting another field value does not change the id

        FieldValue.objects.create(field=standardfield('title'),
                                  record=record,
                                  value='Some title')

        record = Record.objects.get(id=rid)
        self.assertEqual('identifier-407', record.name)
