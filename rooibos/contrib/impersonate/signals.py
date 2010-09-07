import logging
import django.dispatch


user_impersonated = django.dispatch.Signal(providing_args=["user"])
logging.debug("Defined impersonation signal (%s)" % user_impersonated)

