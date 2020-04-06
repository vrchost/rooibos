from rooibos.statistics.functions import register_statistics
from .models import Collection


@register_statistics
def collections():
    model = Collection
    for collection in Collection.objects.all():
        id = collection.id
        values_dict = dict(count=collection.records.count())
        yield model, id, values_dict
