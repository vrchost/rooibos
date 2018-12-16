
class FederatedSearch(object):

    def __init__(self, timeout=10):
        super(FederatedSearch, self).__init__()
        self.timeout = timeout

    def hits_count(self, query):
        raise NotImplementedError

    def get_label(self):
        raise NotImplementedError

    def get_source_id(self):
        raise NotImplementedError

    def get_search_url(self):
        raise NotImplementedError

    @classmethod
    def available(cls):
        return False
