from rooibos.data.models import Record, get_system_field


def get_markers(record):
    markers, created = record.fieldvalue_set.get_or_create(
        field=get_system_field(),
        label='audio-text-sync-markers',
        defaults=dict(
            hidden=True,
        )
    )
    return markers
