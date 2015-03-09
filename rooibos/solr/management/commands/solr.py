from optparse import make_option
from django.core.management.base import BaseCommand
from rooibos.solr import SolrIndex


class Command(BaseCommand):
    help = """
Updates the Solr index

Available commands: optimize|index|reindex|rebuild|clean|clear
"""
    args = 'command'

    option_list = BaseCommand.option_list + (
        make_option('--collection', '-c', dest='collections',
                   action='append',
                    help='Collection identifier (multiple allowed)'),
    )

    def handle(self, *args, **kwargs):
        if not args:
            print self.help
        else:
            collections = map(int, kwargs.get('collections') or list())

            s = SolrIndex()
            for command in args:
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
                else:
                    print "Invalid command %s" % command
