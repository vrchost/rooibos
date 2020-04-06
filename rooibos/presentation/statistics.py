from rooibos.statistics.functions import register_statistics
from .models import Presentation


@register_statistics
def presentations():
    model = Presentation
    values_dict = dict(
        count=Presentation.objects.count(),
        owner_count=Presentation.objects.values('owner').distinct().count(),
        available_count=Presentation.objects.filter(hidden=False).count(),
        available_owner_count=Presentation.objects.filter(
            hidden=False).values('owner').distinct().count())
    yield model, None, values_dict
