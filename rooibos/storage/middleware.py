from django.core.exceptions import MiddlewareNotUsed
from rooibos.access.functions import add_restriction_precedence


class StorageOnStart:

    def __init__(self):

        def download_precedence(a, b):
            if a == 'yes' or b == 'yes':
                return 'yes'
            if a == 'only' or b == 'only':
                return 'only'
            return 'no'
        add_restriction_precedence('download', download_precedence)

        def upload_limit_precedence(a, b):
            return a if (a > b) else b
        add_restriction_precedence('uploadlimit', upload_limit_precedence)

        # Only need to run once
        raise MiddlewareNotUsed
