import logging
import django.dispatch


user_impersonated = django.dispatch.Signal()
logging.debug("Defined impersonation signal (%s)" % user_impersonated)
