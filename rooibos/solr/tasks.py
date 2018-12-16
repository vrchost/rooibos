import logging
from ..celeryapp import app, solr_queue_name
from .functions import SolrIndex


logger = logging.getLogger(__name__)


@app.task(ignore_result=True, queue=solr_queue_name)
def index():
    SolrIndex().index()
