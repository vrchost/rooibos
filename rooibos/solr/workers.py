import logging

from rooibos.solr import SolrIndex
from rooibos.workers.registration import register_worker, run_worker


logger = logging.getLogger(__name__)


@register_worker("solr_index")
def solr_index(data):
    logger.info("Starting solr index")
    count = SolrIndex().index()
    logger.info("solr index done, indexed %d records" % count)


def schedule_solr_index():
    run_worker("solr_index", None)
