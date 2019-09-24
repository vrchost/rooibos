from rooibos.statistics.functions import register_statistics
from .models import Storage


@register_statistics
def storages():
    model = Storage
    for storage in Storage.objects.all():
        id = storage.id
        media = storage.media_set.all()

        total = 0
        for m in media:
            try:
                total += storage.size(m)
            except:
                pass

        values_dict = dict(count=media.count(), size=total)
        yield model, id, values_dict
