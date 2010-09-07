from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^nix/search/', search, name='nasa-nix-search'),
    url(r'^nix/select/', nix_select_record, name='nasa-nix-select'),
)
