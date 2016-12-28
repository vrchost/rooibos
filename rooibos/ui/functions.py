from rooibos.userprofile.views import load_settings, store_settings
from rooibos.access.functions import filter_by_access
from rooibos.presentation.models import Presentation


RECENT_PRESENTATION = 'ui_recent_presentation'


def fetch_current_presentation(user):
    values = load_settings(user, RECENT_PRESENTATION)
    presentation = None
    if RECENT_PRESENTATION in values:
        presentation = filter_by_access(
            user, Presentation, manage=True
        ).filter(id=values[RECENT_PRESENTATION][0])
    return presentation[0] if presentation else None


def store_current_presentation(user, presentation):
    store_settings(user, RECENT_PRESENTATION, presentation.id)
