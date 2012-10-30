DEBUG = False
TEMPLATE_DEBUG = DEBUG
LOGGING_OUTPUT_ENABLED = DEBUG

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'test.sqlite'

CACHE_BACKEND = 'dummy://'

remove_settings = ['DATABASE_OPTIONS']

import tempfile
SCRATCH_DIR = tempfile.mkdtemp()
print "Scratch directory for this test session is %s" % SCRATCH_DIR
