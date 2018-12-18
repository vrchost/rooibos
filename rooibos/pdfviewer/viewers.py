from django import forms
from django.shortcuts import render
from rooibos.viewers import register_viewer, Viewer
from rooibos.data.models import Record


DEFAULT_WIDTH = 1000
DEFAULT_HEIGHT = 800


class PdfViewer(Viewer):

    title = "PDF Viewer"
    weight = 20
    embed_template = 'pdfviewer_embed.html'
    is_embeddable = True
    default_options = dict(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT)

    def get_options_form(self):

        class OptionsForm(forms.Form):
            width = forms.IntegerField(
                max_value=1600, min_value=600, initial=DEFAULT_WIDTH,
                help_text="Enter width in pixels between 600 and 1600"
            )
            height = forms.IntegerField(
                max_value=1600, min_value=600, initial=DEFAULT_HEIGHT,
                help_text="Enter height in pixels between 600 and 1600"
            )

        return OptionsForm

    def embed_script(self, request):

        try:
            width = int(request.GET.get('width', DEFAULT_WIDTH))
        except ValueError:
            width = DEFAULT_WIDTH

        try:
            height = int(request.GET.get('width', DEFAULT_HEIGHT))
        except ValueError:
            height = DEFAULT_HEIGHT

        divid = request.GET.get('id', 'unknown')
        server = '//' + request.META.get(
            'HTTP_X_FORWARDED_HOST', request.META['HTTP_HOST'])

        return render(
            request,
            'pdfviewer.js',
            {
                'media_url': self.pdf_url(),
                'server_url': server,
                'anchor_id': divid,
                'width': width,
                'height': height,
            }
        )

    def pdf_url(self):
        return self.obj.media_set.filter(
            mimetype='application/pdf'
        )[0].get_delivery_url() + '?inline'


@register_viewer('pdfviewer', PdfViewer)
def pdfviewer(obj, request, objid=None):
    if obj:
        if not isinstance(obj, Record):
            return None
    else:
        obj = Record.filter_one_by_access(request.user, objid)
        if not obj:
            return None
    if obj.media_set.filter(mimetype='application/pdf').count() == 0:
        return None
    return PdfViewer(obj, request.user)
