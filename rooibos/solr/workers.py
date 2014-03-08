import logging

from rooibos.solr import SolrIndex
from rooibos.workers.registration import register_worker, run_worker


logger = logging.getLogger("rooibos_solr_workers")


@register_worker("solr_index")
def solr_index(data):
    logger.info("Starting solr index")
    count = SolrIndex().index()
    logger.info("solr index done, indexed %d records" % count)


def schedule_solr_index():
    run_worker("solr_index", None)
