from django_extensions.management.jobs import DailyJob
from datetime import datetime, time
from rooibos.statistics.functions import get_registered_statistics
from rooibos.statistics.models import Activity
from django.contrib.contenttypes.models import ContentType


class Job(DailyJob):
    help = "Collect daily statistics"

    def execute(self):
        now = datetime.now()
        for statistic in get_registered_statistics():
            for model, id, values_dict in statistic():
                Activity.objects.get_or_create(
                    content_type=ContentType.objects.get_for_model(model),
                    object_id=id,
                    date=now.date(),
                    time=time(0, 0, 0),
                    event='daily-statistics',
                    defaults={'data': values_dict},
                )
