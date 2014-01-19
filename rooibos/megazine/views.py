from django.conf import settings
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response
from rooibos.presentation.models import Presentation


def content(request, presentation_id):
    presentation = Presentation.get_by_id_for_request(presentation_id, request)
    if not presentation:
        raise Http404()

    try:
        width = int(request.GET.get('width', 1000))
    except ValueError:
        width = 1000

    items = presentation.items.select_related('record').filter(hidden=False)

    return render_to_response('megazine_content.mz3',
        {'items': items,
         'licensekey': getattr(settings, 'MEGAZINE_PUBLIC_KEY', None),
         'width': width / 2 - 100,
         'height': width - 200,
         },
        context_instance=RequestContext(request))
