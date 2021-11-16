from django.test import TestCase
from rooibos.data.models import Collection, Record, Field, FieldSet, \
    FieldSetField, CollectionItem, standardfield
from .views import _get_browse_fields, _get_facet_fields
from .models import disconnect_signals
from .functions import SolrIndex

from functools import reduce


disconnect_signals()


class BrowseTestCaseBaseClass(TestCase):

    def setUp(self):
        self.collection = Collection.objects.create(
            title='Test Collection', name='test')
        self.titleField = Field.objects.create(label='Title', name='title')
        self.creatorField = Field.objects.create(
            label='Creator', name='creator')
        self.locationField = Field.objects.create(
            label='Location', name='location')
        self.record = Record.objects.create()
        CollectionItem.objects.create(
            collection=self.collection, record=self.record)
        self.record.fieldvalue_set.create(
            field=self.titleField, value='title')
        self.record.fieldvalue_set.create(
            field=self.creatorField, value='creator')
        self.record.fieldvalue_set.create(
            field=self.locationField, value='location')

    def tearDown(self):
        self.collection.delete()
        self.titleField.delete()
        self.creatorField.delete()
        self.locationField.delete()
        self.record.delete()


class BrowseUnrestrictedTestCase(BrowseTestCaseBaseClass):

    def test_browse_field_set(self):
        fields = _get_browse_fields(self.collection.id)
        self.assertEqual(3, len(fields))


class BrowseLimitCollectionTestCase(BrowseTestCaseBaseClass):

    def setUp(self):
        super(BrowseLimitCollectionTestCase, self).setUp()
        self.fieldset = FieldSet.objects.create(
            title='browse-collection-%s' % self.collection.id)
        FieldSetField.objects.create(
            fieldset=self.fieldset, field=self.titleField)

    def tearDown(self):
        self.fieldset.delete()
        super(BrowseLimitCollectionTestCase, self).tearDown()

    def test_browse_field_set_collection_limit(self):
        fields = _get_browse_fields(self.collection.id)
        self.assertEqual(1, len(fields))
        self.assertEqual(self.titleField.id, fields[0].id)


class BrowseLimitGlobalTestCase(BrowseTestCaseBaseClass):

    def setUp(self):
        super(BrowseLimitGlobalTestCase, self).setUp()
        self.fieldset = FieldSet.objects.create(title='browse-collections')
        FieldSetField.objects.create(
            fieldset=self.fieldset, field=self.creatorField)

    def tearDown(self):
        self.fieldset.delete()
        super(BrowseLimitGlobalTestCase, self).tearDown()

    def test_browse_field_set_global_limit(self):
        fields = _get_browse_fields(self.collection.id)
        self.assertEqual(1, len(fields))
        self.assertEqual(self.creatorField.id, fields[0].id)


class FacetsDefaultsTestCase(TestCase):

    def test_default_facets(self):
        fields = _get_facet_fields()
        names = [field.full_name for field in fields]
        self.assertTrue(all(name.startswith('dc.') for name in names))
        self.assertFalse('dc.identifier' in names)


class FacetsCustomTestCase(TestCase):

    def setUp(self):
        self.fieldset = FieldSet.objects.create(title='facet-fields')
        FieldSetField.objects.create(
            fieldset=self.fieldset, field=standardfield('title'))
        FieldSetField.objects.create(
            fieldset=self.fieldset, field=standardfield('creator'))

    def tearDown(self):
        self.fieldset.delete()

    def test_default_facets(self):
        fields = _get_facet_fields()
        names = [field.full_name for field in fields]
        self.assertEqual(2, len(names))
        self.assertTrue('dc.title' in names)
        self.assertTrue('dc.creator' in names)


class CircularCollectionsTestCase(TestCase):

    def test_circular_collections(self):
        group_c = Collection.objects.create(title='C', name='c')
        group_d = Collection.objects.create(title='D', name='d')
        group_e = Collection.objects.create(title='E', name='e')

        group_c.children.add(group_d)
        group_c.children.add(group_e)
        group_c.save()

        group_d.children.add(group_c)
        group_d.save()

        group_e.children.add(group_e)
        group_e.save()

        s = SolrIndex()
        s._build_group_tree()

        def or_set(x, y):
            return set(x) | set(y)

        parents = [group_c.id]
        self.assertEqual(
            2,
            len(reduce(or_set, [s.parent_groups[p] for p in parents], parents))
        )

        parents = [group_d.id]
        self.assertEqual(
            2,
            len(reduce(or_set, [s.parent_groups[p] for p in parents], parents))
        )

        parents = [group_e.id]
        self.assertEqual(
            3,
            len(reduce(or_set, [s.parent_groups[p] for p in parents], parents))
        )
