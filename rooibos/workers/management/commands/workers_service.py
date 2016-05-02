from django.core.management.base import BaseCommand
from rooibos.win32services.workers_service import WorkersService


class Command(BaseCommand):
    help = 'Manages MDID workers service\n\n' \
        'Available command include: start|stop|install|remove'

    def handle(self, *commands, **options):
        if not commands:
            print self.help
        else:
            import win32serviceutil
            win32serviceutil.HandleCommandLine(
                WorkersService,
                serviceClassString=WorkersService.get_class_string(),
                argv=[None] + list(commands)
            )
