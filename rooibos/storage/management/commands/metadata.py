from django.core.management.base import BaseCommand
from django.db import reset_queries
from rooibos.storage.models import Media
from rooibos.util.progressbar import ProgressBar


class Command(BaseCommand):
    help = 'Manages media metadata\nAvailable commands: refresh'
    args = 'command'

    def handle(self, *commands, **options):
        if not commands:
            print(self.help)
        else:
            for command in commands:
                if command == 'refresh':
                    self.refresh()
                else:
                    print("Invalid command %s" % command)

    def refresh(self):
        count = 0
        total = Media.objects.count()
        pb = ProgressBar(total)
        for i in range(0, total, 1000):
            for media in Media.objects.all()[i:i + 1000]:
                media.identify()
                count += 1
                pb.update(count)
            reset_queries()
        pb.done()
