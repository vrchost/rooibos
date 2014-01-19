from django.conf.urls.defaults import *
from views import content

urlpatterns = patterns('',
    url(r'^(?P<presentation_id>[\d]+)/[-\w]+/content/$', content, name='megazine-content'),
)
