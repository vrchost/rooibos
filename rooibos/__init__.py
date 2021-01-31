try:
    from django.core.exceptions import ImproperlyConfigured

    try:
        # This will make sure the app is always imported when
        # Django starts so that shared_task will use this app.
        from .celeryapp import app as celery_app
    except ImproperlyConfigured:
        # Don't break when running outside of configured Django environment
        pass

except ModuleNotFoundError:
    # Running in setup mode
    pass


__all__ = ['celery']
