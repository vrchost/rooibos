from django.test import TestCase
from models import AccumulatedActivity, Activity
from datetime import datetime, date, time
from . import accumulate, get_history

class AccumulatedActivityTest(TestCase):
    
    def test_accumulator(self):

        Activity.objects.create(event='test_accumulator')
        Activity.objects.create(event='test_accumulator')
        Activity.objects.create(event='something_else')
        Activity.objects.create(event='test_accumulator')
        
        rows = accumulate(event='test_accumulator')
        
        self.assertEqual(1, len(rows))        
        self.assertEqual(3, rows[0].count)
        self.assertFalse(rows[0].final)
        
        
    def test_accumulator_dates(self):
        
        Activity.objects.create(event='test2_accumulator', date=date(2009, 5, 1), time=time(1,2,3))
        Activity.objects.create(event='test2_accumulator', date=date(2009, 5, 1), time=time(1,2,4))
        Activity.objects.create(event='something_else', date=date(2009, 5, 1), time=time(1,2,4))
        Activity.objects.create(event='test2_accumulator', date=date(2009, 5, 2), time=time(1,2,0))
        
        rows = accumulate(from_date=date(2009, 5, 1), until_date=date(2009, 5, 2))
        
        self.assertEqual(2, len(rows))
        self.assertTrue(rows[0].final)
        self.assertTrue(rows[1].final)
        
        rows.sort(key=lambda x: x.event)
        
        self.assertEqual(1, rows[0].count)
        self.assertEqual(2, rows[1].count)
        
        
    def test_accumulator_history(self):
    
        object = Activity.objects.create(event='dummy')
    
        Activity.objects.create(event='test3_accumulator', date=date(2009, 5, 1), time=time(1,2,3), content_object=object)
        Activity.objects.create(event='test3_accumulator', date=date(2009, 5, 2), time=time(1,2,3), content_object=object)
        Activity.objects.create(event='test3_accumulator', date=date(2009, 5, 2), time=time(1,2,3), content_object=object)
        Activity.objects.create(event='test3_accumulator', date=date(2009, 5, 4), time=time(1,2,3), content_object=object)
        Activity.objects.create(event='test3_accumulator', date=date(2009, 5, 5), time=time(1,2,3), content_object=object)
        
        history = get_history(event='test3_accumulator',
                              from_date=date(2009, 4, 30),
                              until_date=date(2009, 5, 8),
                              object=object,
                              acc=True)
        
        self.assertEqual([0, 1, 2, 0, 1, 1, 0, 0], history)
        
        history = get_history(event='test3_accumulator',
                            from_date=date(2009, 4, 30),
                            until_date=date(2009, 5, 8),
                            object=object,
                            acc=False)

        self.assertEqual([0, 1, 2, 0, 1, 1, 0, 0], history)
