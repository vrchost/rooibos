from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.views.static import serve
from django.views.decorators.cache import cache_control
from django.http import HttpResponseServerError
from django.template import loader, RequestContext
from rooibos.ui.views import main
from rooibos.access.views import login, logout
from rooibos.legacy.views import legacy_viewer


admin.autodiscover()

apps = filter(lambda a: a.startswith('apps.'), settings.INSTALLED_APPS)
apps_showcases = list(s[5:].replace('.', '-') + '-showcase.html' for s in apps)

# Cache static files
serve = cache_control(max_age=365 * 24 * 3600)(serve)

def handler500_with_context(request):
    template = loader.get_template('500.html')
    return HttpResponseServerError(template.render(RequestContext(request)))

handler404 = getattr(settings, 'HANDLER404', handler404)
handler500 = getattr(settings, 'HANDLER500', handler500_with_context)


def raise_exception():
    raise Exception()


urls = [
    # main page needs SSL because of embedded login form, otherwise CSRF fails
    url(r'^$', main, {'HELP': 'frontpage', 'SSL': True}, name='main'),
    url(r'^about/', direct_to_template, {'template': 'about.html'}, name='about'),
    url(r'^showcases/', direct_to_template, {'HELP': 'showcases',
                                             'template': 'showcases.html',
                                             'extra_context': {'applications': apps_showcases}}, name='showcases'),
    url(r'^login/$', login, {'HELP': 'logging-in', 'SSL': True}, name='login'),
    url(r'^logout/$', logout, {'HELP': 'logging-out', 'next_page': settings.LOGOUT_URL}, name='logout'),
#    url(r'^admin/(.*)', admin.site.root, {'SSL': True}, name='admin'),
    (r'^admin/', include(admin.site.urls)),

    # Legacy URL for presentation viewer in earlier version
    url(r'^viewers/view/(?P<record>\d+)/.+/$', legacy_viewer),

    (r'^ui/', include('rooibos.ui.urls')),
    (r'^acl/', include('rooibos.access.urls')),
    (r'^explore/', include('rooibos.solr.urls')),
    (r'^media/', include('rooibos.storage.urls')),
    (r'^data/', include('rooibos.data.urls')),
    (r'^legacy/', include('rooibos.legacy.urls')),
    (r'^presentation/', include('rooibos.presentation.urls')),
    (r'^viewers/', include('rooibos.viewers.urls')),
    (r'^workers/', include('rooibos.workers.urls')),
    (r'^convert/', include('rooibos.converters.urls')),
    (r'^api/', include('rooibos.api.urls')),
    (r'^profile/', include('rooibos.userprofile.urls')),
    (r'^federated/', include('rooibos.federatedsearch.urls')),
#    (r'^nasa/', include('rooibos.federatedsearch.nasa.urls')),
    (r'^flickr/', include('rooibos.federatedsearch.flickr.urls')),
    (r'^artstor/', include('rooibos.federatedsearch.artstor.urls')),
    (r'^shared/', include('rooibos.federatedsearch.shared.urls')),
    (r'^impersonate/', include('rooibos.contrib.impersonate.urls')),
    (r'^mediaviewer/', include('rooibos.mediaviewer.urls')),
    (r'^megazine/', include('rooibos.megazine.urls')),
    (r'^pdfviewer/', include('rooibos.pdfviewer.urls')),
    (r'^pptexport/', include('rooibos.pptexport.urls')),
    (r'^audiotextsync/', include('rooibos.audiotextsync.urls')),

    url(r'^favicon.ico$', serve, {'document_root': settings.STATIC_DIR, 'path': 'images/favicon.ico'}),
    url(r'^robots.txt$', serve, {'document_root': settings.STATIC_DIR, 'path': 'robots.txt'}),
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_DIR}, name='static'),

    url(r'^exception/$', raise_exception),
    ]

for app in apps:
    if not '.' in app[5:]:
        urls.append(url(r'^%s/' % app[5:], include('%s.urls' % app)))

urlpatterns = patterns('', *urls)
