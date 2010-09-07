from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.storage.models import Media

class PackagePresentation(object):

    title = "QuickTime Player"

    def __init__(self):
        pass

    def analyze(self, obj, user):
        if not isinstance(obj, Media) or obj.mimetype != 'video/quicktime':
            return NO_SUPPORT
        else:
            return FULL_SUPPORT

    def url(self):
        return url(r'^quicktime-player/(?P<recordid>[\d]+)/(?P<recordname>[-\w]+)/(?P<mediaid>[\d]+)/(?P<medianame>[-\w]+)/$',
                   self.player, name='viewers-quicktime-player')

    def url_for_obj(self, obj):
        if not obj.record:
            return None
        return reverse('viewers-quicktime-player', kwargs={'recordid': obj.record.id,
                                                           'recordname': obj.record.name,
                                                           'mediaid': obj.record.id,
                                                           'medianame': obj.record.name})

    def player(self, request, recordid, mediaid, recordname, medianame):
        return HttpResponse(content='Quicktime player for %s goes here!' % medianame)

    def inline(self, obj, options=None):
        return ''

#url = media.get_absolute_url()
#        if url.startswith('http'):
#            return '<a href="%s">%s</a>' % (url, 'Download Quicktime Video')
#        else:
#            return """
#<script src='/static/viewers/qtviewer/AC_QuickTime.js' language='JavaScript' type='text/javascript'></script>
#<script language='JavaScript' type='text/javascript'>
#QT_WriteOBJECT('/static/viewers/qtviewer/watchnow.mov','91','15','',
#'controller','false',
#'autoplay','true',
#'loop','false',
#'cache','true',
#'href','%s',
#'target','quicktimeplayer',
#'align','absmiddle',
#'vspace','5',
#'style','margin-top: 5px; margin-bottom: 5px'
#);
#</script>""" % (url)
