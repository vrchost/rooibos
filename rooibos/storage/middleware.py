from django.core.exceptions import MiddlewareNotUsed
import logging
from models import Storage, Media

class StorageOnStart:

    def __init__(self):

        try:
            # Derivative storage no longer used, remove all from database
            storage_ids = list(Media.objects.filter(
                master__isnull=False
                ).values_list('storage__id', flat=True).distinct())
            storage_ids.extend(Storage.objects.exclude(
                id__in=Media.objects.all().values('storage__id')).filter(
                base__startswith='d:/mdid/scratch/').values_list('id', flat=True))
            for storage in Storage.objects.filter(derivative__isnull=False).exclude(derivative__in=storage_ids):
                storage_ids.append(storage.derivative)
            for storage in Storage.objects.filter(id__in=storage_ids):
                storage.delete()
        except Exception, ex:
            # Clean up failed, log exception and continue
            logging.error("Derivative storage cleanup failed: %s" % ex)
            pass

        from rooibos.access import add_restriction_precedence

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
