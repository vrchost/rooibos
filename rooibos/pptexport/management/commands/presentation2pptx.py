import datetime
import os
import sys
import re

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from rooibos.presentation.models import Presentation
from rooibos.pptexport.functions import PowerPointGenerator, COLORS


class Command(BaseCommand):

    help = 'Export presentation as PPTX file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list', '-l',
            dest='list',
            action='store_true',
            help='List presentations that would be exported'
        )
        parser.add_argument(
            '--days', '-d',
            dest='days',
            type=int,
            metavar='N',
            help='Export presentations changed in the past N days'
        )
        parser.add_argument(
            '--output-dir', '-o',
            dest='output_dir',
            help='Target directory for files'
        )
        parser.add_argument(
            '--id', '-i',
            dest='id',
            type=int,
            help='Identifier of a specific presentation to export'
        )
        parser.add_argument(
            '--min-id', '-n',
            dest='min_id',
            type=int,
            help='Minimum identifier of presentations to export '
            '(to batch export)'
        )
        parser.add_argument(
            '--max-id', '-x',
            dest='max_id',
            type=int,
            help='Maximum identifier of presentations to export '
            '(to batch export)'
        )
        parser.add_argument(
            '--color', '-c',
            dest='color',
            default='white',
            choices=COLORS.keys(),
            help='Background color'
        )
        parser.add_argument(
            '--titles', '-t',
            dest='titles',
            action='store_true',
            help='Add slide titles'
        )
        parser.add_argument(
            '--metadata', '-m',
            dest='metadata',
            action='store_true',
            help='Add slide metadata'
        )

    def get_admin_user(self):

        admins = User.objects.filter(is_superuser=True)[:1]
        if len(admins) == 1:
            return admins[0]
        else:
            print("No administrative user account found", file=sys.stderr)
            sys.exit(1)

    def get_filename(self, presentation):

        def clean(s):
            return re.sub('[^a-zA-Z0-9@._-]', '_', s)

        return "%s-%s-%d.pptx" % (
            clean(presentation.owner.username),
            clean(presentation.title),
            presentation.id,
        )

    def handle(self, *config_files, **options):

        admin = self.get_admin_user()
        template = options.get('template')

        presentations = Presentation.objects.all().select_related(
            'owner').order_by('id')

        if options.get('id'):
            presentations = presentations.filter(id=options['id'])
        if options.get('days', 0) > 0:
            since = datetime.datetime.combine(
                datetime.date.today() - datetime.timedelta(options['days']),
                datetime.time.min)
            print("Exporting presentations modified since %s" % since, file=sys.stderr)
            presentations = presentations.filter(modified__gte=since)
        if options.get('min_id'):
            presentations = presentations.filter(id__gte=options['min_id'])
        if options.get('max_id'):
            presentations = presentations.filter(id__lte=options['max_id'])

        print("Exporting %d presentations using template %s" % (
            presentations.count(),
            template,
        ), file=sys.stderr)

        for presentation in presentations:
            filename = self.get_filename(presentation)
            print(filename)
            if not options.get('list'):
                g = PowerPointGenerator(presentation, admin)
                if options.get('output_dir'):
                    filename = os.path.join(options['output_dir'], filename)
                g.generate(
                    filename,
                    options.get('color'),
                    options.get('titles'),
                    options.get('metadata'),
                )
