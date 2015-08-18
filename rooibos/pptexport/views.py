from __future__ import with_statement
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from zipfile import ZipFile
from functions import PowerPointGenerator
from rooibos.presentation.models import Presentation
import os



def thumbnail(request, template):
    filename = os.path.join(os.path.dirname(__file__), 'pptx_templates', template + '.pptx')
    if not os.path.isfile(filename):
        raise Http404()
    template = ZipFile(filename, mode='r')
    return HttpResponse(content=template.read('docProps/thumbnail.jpeg'), mimetype='image/jpg')


def download(request, id, template):

    return_url = request.GET.get('next', reverse('presentation-browse'))
    presentation = Presentation.get_by_id_for_request(id, request)
    if not presentation:
        return HttpResponseRedirect(return_url)

    g = PowerPointGenerator(presentation, request.user)
    filename = os.tempnam()
    try:
        g.generate(template, filename)
        with open(filename, mode="rb") as f:
            response = HttpResponse(content=f.read(),
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        response['Content-Disposition'] = 'attachment; filename=%s.pptx' % presentation.name
        return response
    finally:
        try:
            os.unlink(filename)
        except:
            pass
