from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseNotAllowed
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
from rooibos.data.models import *
from rooibos.viewers.functions import get_viewer_by_name
import random
from datetime import datetime

def imageviewer_login(request):    
    
    if settings.SECURE_LOGIN and not request.is_secure():
        return HttpResponseForbidden()
    
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    user = request.POST.get('userID')
    password = request.POST.get('password')
    
    if False: # check for user credentials
        resultcode = 'INVALIDCREDENTIALS'
        errormessage = 'The specified user/password combination is not valid.'
    elif False: # check for imageviewer access permission
        resultcode = 'IMAGEVIEWERACCESSDENIED'
        errormessage = 'You do not have permission to use the ImageViewer with this server.'
    else:
        resultcode = 'SUCCESS'
        errormessage = 'n/a'
        sessiontoken = 'user_%s-%s' % (random.randint(100000000, 999999999), random.randint(100000000, 999999999))
        slideshows = {'[MAIN]':
            ({'id': 123, 'title': 'Testing', 'created': datetime.now(), 'modified': datetime.now(), 'archived': True},
             {'id': 124, 'title': 'More Testing', 'created': datetime.now(), 'modified': datetime.now(), 'archived': False},
            )}
                    
    return render_to_response('imageviewer_login.xml',
                              {'namespace': settings.WEBSERVICE_NAMESPACE,
                               'errormessage': errormessage,
                               'resultcode': resultcode,
                               'sessiontoken': sessiontoken,
                               'slideshows': slideshows},
                              context_instance=RequestContext(request),
                              mimetype='text/xml')


def imageviewer_getslideshow(request):

#    if request.method != 'POST':
#        return HttpResponseNotAllowed(['POST'])

    slideshowID = request.POST.get('slideshowID')
    sessiontoken = request.POST.get('sessiontoken')

    if False: # check if slideshow is empty
        resultcode = 'EMPTYSLIDESHOW'
        errormessage = 'Slideshow is empty.'
    else:
        resultcode = 'SUCCESS'
        errormessage = None
        collection = get_object_or_404(Collection, name='admins-test')
        # todo: medium size is hardcoded, media id is hardcoded as zero
        slides = [{'url': reverse('storage-retrieve', kwargs={'recordid': r.id, 'record': r.name, 'mediaid': 0, 'media': 'medium'}).split('/', 2)[2] + "?dummy",
                   'id': r.id,
                   'imageid': r.id,
                   'collectionid': collection.id,
                   'filename': '%s.jpg' % r.name,
                   'fields': [{'label': f.label, 'value': f.value}
                              for f in r.get_fieldvalues(collection=collection, filter_hidden=True)]
                    } for r in collection.all_records]

    return render_to_response('imageviewer_slideshow.xml',
                              {'namespace': settings.WEBSERVICE_NAMESPACE,
                               'resultcode': resultcode,
                               'errormessage': errormessage,
                               'slides': slides},
                              context_instance=RequestContext(request),
                              mimetype='text/xml')



# Handler for old presentation view URLs
def legacy_viewer(request, record):
    viewer = get_viewer_by_name('presentationviewer')
    return redirect(viewer(None, request, record).url())
