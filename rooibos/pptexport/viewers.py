
from django import forms
from django.template.loader import render_to_string

from rooibos.pptexport.functions import COLORS
from rooibos.viewers import register_viewer, Viewer
from rooibos.presentation.models import Presentation
import os


class PowerPointExportViewer(Viewer):

    title = "PowerPoint"
    weight = 15

    def get_options_form(self):
        class OptionsForm(forms.Form):
            color = forms.ChoiceField(
                required=False,
                initial='white',
                label='Background color',
                choices=((c, c) for c in COLORS.keys()),
                help_text='Slide background color',
            )
            titles = forms.BooleanField(
                required=False,
                label='Slide titles',
                help_text='Add titles to slides',
            )
            metadata = forms.BooleanField(
                required=False,
                label='Slide metadata',
                help_text='Add metadata to slide',
            )
        return OptionsForm

    def embed_code(self, request, options):
        return render_to_string(
            "pptexport_download.html",
            {
                'viewer': self,
                'obj': self.obj,
                'options': options,
                'request': request,
            }
        )


@register_viewer('powerpointexportviewer', PowerPointExportViewer)
def powerpointexportviewer(obj, request, objid=None):
    if obj:
        if not isinstance(obj, Presentation):
            return None
    else:
        obj = Presentation.get_by_id_for_request(objid, request)
        if not obj:
            return None
    return PowerPointExportViewer(obj, request.user)
