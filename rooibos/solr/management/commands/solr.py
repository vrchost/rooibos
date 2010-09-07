from django.core.management.base import BaseCommand
from rooibos.solr import SolrIndex

class Command(BaseCommand):
    help = 'Updates the Solr index\nAvailable commands: optimize|index|reindex|clear'
    args = 'command'

    def handle(self, *commands, **options):
        if not commands:
            print self.help
        else:
            s = SolrIndex()
            for command in commands:
                if command == 'optimize':
                    s.optimize()
                elif command == 'index':
                    s.index(verbose=True)
                elif command == 'reindex':
                    s.clear()
                    s.index(verbose=True, all=True)
                elif command == 'clear':
                    s.clear()
                else:
                    print "Invalid command %s" % command
                