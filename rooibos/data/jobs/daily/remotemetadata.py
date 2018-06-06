from django_extensions.management.jobs import DailyJob
from ...remotemetadata import fetch_remote_metadata


class Job(DailyJob):
    help = "Fetch and update remote metadata"

    def execute(self):
        fetch_remote_metadata()
