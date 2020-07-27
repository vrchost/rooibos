from django.conf.urls import url, handler404, include
from django.contrib import admin
from django.conf import settings
from django.views.generic.base import TemplateView
from django.views.static import serve
from django.views.decorators.cache import cache_control
from django.http import HttpResponseServerError
from django.template import loader
from rooibos.ui.views import main
from rooibos.access.views import login, logout
from rooibos.legacy.views import legacy_viewer
from rooibos.version import getVersion


admin.autodiscover()

apps = [a for a in settings.INSTALLED_APPS if a.startswith('apps.')]
apps_showcases = list(s[5:].replace('.', '-') + '-showcase.html' for s in apps)

# Cache static files
serve = cache_control(max_age=365 * 24 * 3600)(serve)


def handler500_with_context(request):
    template = loader.get_template('500.html')
    return HttpResponseServerError(template.render(request=request))


handler404 = getattr(settings, 'HANDLER404', handler404)
handler500 = getattr(settings, 'HANDLER500', handler500_with_context)


def raise_exception():
    raise Exception()


class ShowcasesView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(ShowcasesView, self).get_context_data(**kwargs)
        context.update({
            'applications': apps_showcases,
        })
        return context


urls = [
    url(r'^$', main, {'HELP': 'frontpage'}, name='main'),
    url(
        r'^about/',
        TemplateView.as_view(template_name='about.html'),
        kwargs={'version': getVersion()},
        name='about'
    ),
    url(
        r'^showcases/',
        ShowcasesView.as_view(template_name='showcases.html'),
        name='showcases'
    ),

    url(r'^admin/', include(admin.site.urls)),

    # Legacy URL for presentation viewer in earlier version
    url(r'^viewers/view/(?P<record>\d+)/.+/$', legacy_viewer),

    url(r'^ui/', include('rooibos.ui.urls')),
    url(r'^acl/', include('rooibos.access.urls')),
    url(r'^explore/', include('rooibos.solr.urls')),
    url(r'^media/', include('rooibos.storage.urls')),
    url(r'^data/', include('rooibos.data.urls')),
    url(r'^legacy/', include('rooibos.legacy.urls')),
    url(r'^presentation/', include('rooibos.presentation.urls')),
    url(r'^viewers/', include('rooibos.viewers.urls')),
    url(r'^workers/', include('rooibos.workers.urls')),
    url(r'^api/', include('rooibos.api.urls')),
    url(r'^profile/', include('rooibos.userprofile.urls')),
    url(r'^federated/', include('rooibos.federatedsearch.urls')),
    url(r'^flickr/', include('rooibos.federatedsearch.flickr.urls')),
    url(r'^artstor/', include('rooibos.federatedsearch.artstor.urls')),
    url(r'^shared/', include('rooibos.federatedsearch.shared.urls')),
    url(r'^impersonate/', include('rooibos.impersonate.urls')),
    url(r'^works/', include('rooibos.works.urls')),
    url(r'^pdfviewer/', include('rooibos.pdfviewer.urls')),
    url(r'^pptexport/', include('rooibos.pptexport.urls')),

    url(
        r'^favicon.ico$',
        serve,
        {
            'document_root': settings.STATIC_ROOT,
            'path': 'images/favicon.ico'
        }
    ),
    url(
        r'^robots.txt$',
        serve,
        {
            'document_root': settings.STATIC_ROOT,
            'path': 'robots.txt'
        }
    ),
    url(
        r'^static/(?P<path>.*)$',
        serve,
        {
            'document_root': settings.STATIC_ROOT
        },
        name='static'
    ),

    url(r'^exception/$', raise_exception),
]

try:
    import django_shibboleth  # noqa
    urls.append(
        url(r'^shibboleth/', include('django_shibboleth.urls')),
    )
except ImportError:
    pass


if getattr(settings, 'CAS_SERVER_URL', None):
    import django_cas_ng.views
    urls += [
        url(
            r'^login/$',
            django_cas_ng.views.login,
            {
                'HELP': 'logging-in',
            },
            name='login'
        ),
        url(
            r'^local-login/$',
            login,
            {
                'HELP': 'logging-in',
            },
            name='local-login'
        ),
        url(
            r'^logout/$',
            django_cas_ng.views.logout,
            {
                'HELP': 'logging-out',
                'next_page': settings.LOGOUT_URL
            },
            name='logout'
        ),
    ]
else:
    urls += [
        url(
            r'^login/$',
            login,
            {
                'HELP': 'logging-in',
            },
            name='login'
        ),
        url(
            r'^logout/$',
            logout,
            {
                'HELP': 'logging-out',
                'next_page': settings.LOGOUT_URL
            },
            name='logout'
        ),
    ]

for app in apps:
    if '.' not in app[5:]:
        urls.append(url(r'^%s/' % app[5:], include('%s.urls' % app)))


urlpatterns = urls
