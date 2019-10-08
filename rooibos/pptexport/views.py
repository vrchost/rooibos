from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from zipfile import ZipFile
from .functions import PowerPointGenerator
from rooibos.presentation.models import Presentation
import os
import tempfile


def thumbnail(request, template):
    filename = os.path.join(
        os.path.dirname(__file__), 'pptx_templates', template + '.pptx')
    if not os.path.isfile(filename):
        raise Http404()
    template = ZipFile(filename, mode='r')
    return HttpResponse(
        content=template.read('docProps/thumbnail.jpeg'),
        content_type='image/jpg'
    )


def download(request, id, template):

    return_url = request.GET.get('next', reverse('presentation-browse'))
    presentation = Presentation.get_by_id_for_request(id, request)
    if not presentation:
        return HttpResponseRedirect(return_url)

    g = PowerPointGenerator(presentation, request.user)
    with tempfile.TemporaryFile() as zipfile:
        g.generate(template, zipfile)
        zipfile.seek(0)
        response = HttpResponse(
            content=zipfile.read(),
            content_type='application/vnd.openxmlformats-officedocument'
            '.presentationml.presentation'
        )
        response['Content-Disposition'] = \
            'attachment; filename=%s.pptx' % presentation.name
        return response
