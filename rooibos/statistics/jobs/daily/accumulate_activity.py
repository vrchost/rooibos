from django_extensions.management.jobs import DailyJob
from datetime import timedelta
from rooibos.statistics.functions import accumulate
from rooibos.statistics.models import AccumulatedActivity


class Job(DailyJob):
    help = "Accumulate activity statistics"

    def execute(self):

        try:
            latest = AccumulatedActivity.objects.all().order_by('-date')[0]
            from_date = latest.date - timedelta(1)
        except IndexError:
            from_date = None

        accumulate(from_date=from_date)
