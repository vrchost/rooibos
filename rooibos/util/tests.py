from django.test import TestCase
from rooibos.data.models import Collection, Record
from rooibos.storage.models import Media, Storage


class UniqueSlugTestCase(TestCase):

    def test_long_unique_slugs(self):
        for i in range(100):
            Collection.objects.create(title='T' * 50)
        for i in range(10):
            Collection.objects.create(title='T' * 100)

    def test_unique_slugs(self):
        g = Collection.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs', g.name)

        g = Collection.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs-2', g.name)

        g = Collection.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs-3', g.name)

    def test_unique_with_something_slugs(self):
        r1 = Record.objects.create()
        r2 = Record.objects.create()

        s = Storage.objects.create(title='Test', system='online')

        m1 = Media.objects.create(record=r1, name='thumb', url='m1', storage=s)
        m2 = Media.objects.create(record=r2, name='thumb', url='m2', storage=s)

        self.assertEqual('thumb', m1.name)
        self.assertEqual('thumb', m2.name)

        m2b = Media.objects.create(
            record=r2, name='thumb', url='m2b', storage=s)

        self.assertEqual('thumb-2', m2b.name)
