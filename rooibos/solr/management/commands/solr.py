import pprint

from django.core.management.base import BaseCommand
from rooibos.solr.functions import SolrIndex


def dump(docs):
    pprint.pprint(docs)


class Command(BaseCommand):
    help = "Updates the Solr index"

    def add_arguments(self, parser):
        parser.add_argument('command', nargs='+',
                            help='optimize|index|reindex|rebuild|clean|clear')
        parser.add_argument(
            '--collection', '-c',
            dest='collections',
            action='append',
            help='Collection identifier (multiple allowed)'
        )
        parser.add_argument(
            '--records', '-r',
            dest='records',
            action='append',
            help='Record identifier (multiple allowed)'
        )

    def handle(self, *args, **kwargs):
        collections = list(map(int, kwargs.get('collections') or list()))
        records = list(map(int, kwargs.get('records') or list()))

        s = SolrIndex()
        for command in kwargs['command']:
            if command == 'optimize':
                s.optimize()
            elif command == 'index':
                s.index(verbose=True)
            elif command == 'reindex':
                s.index(verbose=True, all=True, collections=collections)
                s.clear_missing(verbose=True)
            elif command == 'clean':
                s.clear_missing(verbose=True)
            elif command == 'rebuild':
                s.clear()
                s.index(verbose=True, all=True, collections=collections)
            elif command == 'clear':
                s.clear()
            elif command == 'dump':
                s.index(record_ids=records, handler=dump)
            else:
                print("Invalid command %s" % command)
