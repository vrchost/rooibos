from django.db.models import Count
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from models import AccumulatedActivity, Activity
from datetime import datetime, date, timedelta

def accumulate(event=None, from_date=None, until_date=None, object=None):
    today = datetime.now().date()
    query = Activity.objects.all()
    if event:
        query = query.filter(event=event)
    if from_date:
        query = query.filter(date__gte=from_date)
    if until_date:
        query = query.filter(date__lt=until_date)
    if object:
        content_type = ContentType.objects.get_for_model(object)
        query = query.filter(content_type=content_type, object_id=object.id)
    rows = []
    for data in query.values('content_type','object_id','date','event').annotate(count=Count('id')):
        # query.values() returns dates as strings for some databases
        if type(data['date']) != date:
            data['date'] = datetime.strptime(data['date'], '%Y-%m-%d').date()
        # query.values() does not return objects for foreign keys, only ids
        if data['content_type']:
            data['content_type'] = ContentType.objects.get_for_id(data['content_type'])
        accumulated, created = AccumulatedActivity.objects.get_or_create(
            content_type=data['content_type'],
            object_id=data['object_id'],
            date=data['date'],
            event=data['event'],
            defaults=dict(count=0))
        accumulated.final = data['date'] < today
        accumulated.count = data['count']
        accumulated.save()
        rows.append(accumulated)
    return rows


def assure_accumulation(from_date, until_date=None, events=None, callback=None):
    activity = AccumulatedActivity.objects.filter(final=False, date__gte=from_date)
    if until_date:
        activity = activity.filter(date__lt=until_date)
    check = activity.distinct().values_list('date', 'event')
    if events:
        check = check.filter(event__in=events)
    for step, (date, event) in enumerate(check):
        if callback:
            callback(date, event, step, len(check))
        accumulate(event=event, from_date=date, until_date=date + timedelta(1))


def get_history(event, from_date, until_date=None, object=None, acc=False):

    if acc:
        rows = accumulate(event, from_date, until_date, object)
    else:
        rows = AccumulatedActivity.objects.filter(event=event, date__gte=from_date)
        if until_date:
            rows = rows.filter(date__lt=until_date)
        if object:
            content_type = ContentType.objects.get_for_model(object)
            rows = rows.filter(content_type=content_type, object_id=object.id)

    sum = dict()
    for row in rows:
        sum[row.date] = sum.get(row.date, 0) + row.count

    if not until_date:
        until_date=datetime.now().date() + timedelta(1)

    result = []
    date = from_date
    while date < until_date:
        result.append(sum.get(date, 0))
        date += timedelta(1)

    return result



registered_statistics = []

def discover_statistics():
    if not registered_statistics:
        for app in settings.INSTALLED_APPS:
            try:
                module = __import__(app + ".statistics")
            except ImportError:
                pass

def get_registered_statistics():
    discover_statistics()
    return registered_statistics

def register_statistics(func):
    registered_statistics.append(func)
    return func
