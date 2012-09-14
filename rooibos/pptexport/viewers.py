from __future__ import with_statement
from django import forms
from django.template.loader import render_to_string
from rooibos.viewers import register_viewer, Viewer
from rooibos.presentation.models import Presentation
import os


class PowerPointExportViewer(Viewer):

    title = "PowerPoint"
    weight = 15

    templates = [
        (template[:-5], template[:-5])
        for template in os.listdir(os.path.join(os.path.dirname(__file__),
                                   'pptx_templates'))
        if template.endswith('.pptx')
    ]

    def get_options_form(self):
        class OptionsForm(forms.Form):
            template = forms.ChoiceField(choices=self.templates,
                help_text="Select the PowerPoint template to use.")
        return OptionsForm

    def embed_code(self, request, options):
        return render_to_string("pptexport_download.html", {
            'viewer': self,
            'obj': self.obj,
            'options': options,
            'default_template': self.templates and self.templates[0][0],
            'request': request,
        })


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
