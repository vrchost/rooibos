from django_extensions.management.jobs import DailyJob
from ...remotemetadata import fetch_remote_metadata


class Job(DailyJob):
    help = "Accumulate activity statistics"

    def execute(self):
        fetch_remote_metadata()
