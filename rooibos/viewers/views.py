from functions import get_viewer_by_name
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseForbidden
from django.template import RequestContext


def viewer_shell(request, viewer, objid, template='viewers_shell.html'):

    viewer_cls = get_viewer_by_name(viewer)
    if not viewer_cls:
        raise Http404()
    viewer = viewer_cls(None, request, objid=objid)
    if not viewer:
        if not request.user.is_authenticated():
            return redirect(reverse('login') +
                            '?next=' + request.get_full_path())
        raise Http404()

    response = viewer.view(request)
    if response:
        return response

    options_form_cls = viewer.get_options_form()
    if options_form_cls:
        options_form = options_form_cls(request.GET)
        options = options_form.cleaned_data if options_form.is_valid() else viewer.default_options
    else:
        options_form = None
        options = viewer.default_options

    return render_to_response(
        template,
        {
            'viewer': viewer,
            'next': request.GET.get('next'),
            'embed_code': viewer.embed_code(request, options),
            'options_form': options_form,
        },
        context_instance=RequestContext(request))


def viewer_script(request, viewer, objid):

    viewer_cls = get_viewer_by_name(viewer)
    if not viewer_cls:
        raise Http404()
    viewer = viewer_cls(None, request, objid=objid)
    if not viewer:
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        else:
            raise Http404()

    try:
        return viewer.embed_script(request)
    except Http404:
        if not request.user.is_authenticated():
            return HttpResponseForbidden()
        raise


# Handler for legacy URL for videos embedded using previous versions of MDID3
def legacy_embedded_video(request, record, media):
    return redirect(reverse(
        'viewers-viewer-script',
        args=('mediaplayer', record)) + '?' +
        'id=player-%(record)s-%(media)s&media=%(media)s&autoplay=%(autoplay)s' %
        {
            'record': record,
            'media': media,
            'autoplay': request.GET.has_key('autoplay'),
        })
