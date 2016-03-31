from django.conf import settings as _settings
from django.utils.functional import SimpleLazyObject
from rooibos.util import IterableLazyObject
from rooibos.data.models import Record
from rooibos.ui.functions import fetch_current_presentation


def settings(request):
    """
    Returns selected context variables based on application settings
    """

    old_vars = (
        'STATIC_DIR',
        'PRIMARY_COLOR',
        'SECONDARY_COLOR',
        'CUSTOM_TRACKER_HTML'
    )
    return dict(
        (var, getattr(_settings, var, ''))
        for var in getattr(_settings, 'EXPOSE_TO_CONTEXT', old_vars)
    )


def selected_records(request):

    selected = request.session.get('selected_records', ())
    if selected:
        unsorted_records = dict(
            (r.id, r)
            for r in Record.filter_by_access(request.user, *selected)[:200])
        # put records back in correct order
        records = []
        for rid in selected:
            if rid in unsorted_records:
                records.append(unsorted_records[rid])
    else:
        records = None

    return {
        'selected_records_count': len(selected),
        'selected_records': records,
    }


def current_presentation(request):

    presentation = SimpleLazyObject(
        lambda: fetch_current_presentation(request.user))

    def get_presentation_records():
        try:
            return list(
                presentation.items.values_list('record_id', flat=True)
                .distinct()
            )
        except AttributeError:
            return []

    presentation_records = IterableLazyObject(get_presentation_records)

    return {
        'current_presentation': presentation,
        'current_presentation_records': presentation_records,
    }
