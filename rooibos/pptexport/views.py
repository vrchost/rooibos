import tempfile

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect

from rooibos.presentation.models import Presentation
from .functions import PowerPointGenerator, COLORS


def download(request, id):

    return_url = request.GET.get('next', reverse('presentation-browse'))
    presentation = Presentation.get_by_id_for_request(id, request)
    if not presentation:
        return HttpResponseRedirect(return_url)

    color = request.GET.get('color')
    if not color in COLORS.keys():
        color = sorted(COLORS.keys())[0]
    titles = request.GET.get('titles', 'yes') == 'yes'
    metadata = not (request.GET.get('metadata', 'no') != 'yes')

    g = PowerPointGenerator(presentation, request.user)
    with tempfile.TemporaryFile() as zipfile:
        g.generate(zipfile, color, titles, metadata)
        zipfile.seek(0)
        response = HttpResponse(
            content=zipfile.read(),
            content_type='application/vnd.openxmlformats-officedocument'
            '.presentationml.presentation'
        )
        response['Content-Disposition'] = \
            'attachment; filename=%s.pptx' % presentation.name
        return response
