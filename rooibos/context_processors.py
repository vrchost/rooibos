from django.conf import settings as _settings
from rooibos.data.models import Record, Collection
from rooibos.access import accessible_ids

def settings(request):
    """
    Returns selected context variables based on application settings
    """

    return {
        'STATIC_DIR': _settings.STATIC_DIR,
        'PRIMARY_COLOR': _settings.PRIMARY_COLOR,
        'SECONDARY_COLOR': _settings.SECONDARY_COLOR,
    }


def selected_records(request):
    
    selected = request.session.get('selected_records', ())
    if selected:
        records = Record.objects.filter(id__in=selected, collection__id__in=accessible_ids(request.user, Collection))[:200]
    else:
        records = None
    
    return {
        'selected_records_count': len(selected),
        'selected_records': records,
    }
    