from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.conf import settings
from django.db.models import Q
from rooibos.presentation.models import Presentation
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.access import accessible_ids, filter_by_access
from rooibos.storage import get_image_for_record
from rooibos.data.models import Record, Collection
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.colors import white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.frames import Frame
from reportlab.platypus import flowables
import Image


def getStyleSheet():
    """Returns a stylesheet object"""
    stylesheet = StyleSheet1()

    stylesheet.add(ParagraphStyle(name='Normal',
                                  fontName='Times-Roman',
                                  fontSize=8,
                                  leading=10,
                                  spaceAfter=18))
    stylesheet.add(ParagraphStyle(name='SlideNumber',
                                  parent=stylesheet['Normal'],
                                  alignment=TA_RIGHT,
                                  fontSize=6,
                                  leading=8,
                                  rightIndent=3,
                                  spaceAfter=0))
    stylesheet.add(ParagraphStyle(name='Heading',
                                  parent=stylesheet['Normal'],
                                  fontSize=20,
                                  leading=24,
                                  alignment=TA_CENTER,
                                  spaceAfter=0))
    stylesheet.add(ParagraphStyle(name='SubHeading',
                                  parent=stylesheet['Normal'],
                                  fontSize=16,
                                  leading=20,
                                  alignment=TA_CENTER))
    return stylesheet


class PrintView(object):

    title = "Print View"
    weight = 40
    
    def __init__(self):
        pass
    
    def analyze(self, obj, user):
        if not isinstance(obj, Presentation):
            return NO_SUPPORT
        items = obj.cached_items()
        valid = filter(lambda i: not i.type or i.hidden, items)
        if len(valid) == 0:
            return NO_SUPPORT
        elif len(valid) < len(items):
            return PARTIAL_SUPPORT
        else:
            return FULL_SUPPORT
    
    def url(self):
        return url(r'^printview/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.view, name='viewers-printview')
    
    def url_for_obj(self, obj):
        return reverse('viewers-printview', kwargs={'id': obj.id, 'name': obj.name})
    
    def view(self, request, id, name):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        presentation = Presentation.get_by_id_for_request(id, request)
        if not presentation:
            return HttpResponseRedirect(return_url)

        passwords = request.session.get('passwords', dict())

        response = HttpResponse(mimetype='application/pdf')

        pagesize = getattr(pagesizes, settings.PDF_PAGESIZE)
        width, height = pagesize
        
        class DocTemplate(BaseDocTemplate):
            def afterPage(self):
                self.handle_nextPageTemplate('Later')

        def column_frame(left):
            return Frame(left, inch / 2,
                           width=width / 2 - 0.75 * inch, height = height - inch,
                          leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0, showBoundary=False)
        
        def prepare_first_page(canvas, document):
            p1 = Paragraph(presentation.title, styles['Heading'])
            p2 = Paragraph(presentation.owner.get_full_name(), styles['SubHeading'])
            avail_width = width - inch
            avail_height = height - inch
            w1, h1 = p1.wrap(avail_width, avail_height)
            w2, h2 = p2.wrap(avail_width, avail_height)
            f = Frame(inch / 2, inch / 2, width - inch, height - inch,
                      leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
            f.addFromList([p1, p2], canvas)

            document.pageTemplate.frames[0].height -= h1 + h2 + inch / 2
            document.pageTemplate.frames[1].height -= h1 + h2 + inch / 2

            canvas.saveState()
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.line(width / 2, inch / 2, width / 2, height - inch - h1 - h2)
            canvas.restoreState()
        
        def prepare_later_page(canvas, document):
            canvas.saveState()
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.line(width / 2, inch / 2, width / 2, height - inch / 2)
            canvas.restoreState()
        
        
        styles = getStyleSheet()
        
        items = presentation.items.filter(hidden=False)
        
        content = []
        
        for index, item in enumerate(items):
            text = []
            values = item.get_fieldvalues(owner=request.user)
            for value in values:
                text.append('<b>%s</b>: %s<br />' % (value.resolved_label, value.value))
            annotation = item.annotation
            if annotation:
                text.append('<b>%s</b>: %s<br />' % ('Annotation', annotation))
            p = Paragraph(''.join(text), styles['Normal'])
            image = get_image_for_record(item.record, presentation.owner, 100, 100, passwords, force_local=True)
            if image:
                try:
                    i = flowables.Image(image.get_absolute_file_path(),
                                        width=1.5 * inch * (image.width or 100) / 100,
                                        height=1.5 * inch * (image.height or 100) / 100)
                    p = flowables.ParagraphAndImage(p, i)
                except IOError:
                    pass
            content.append(flowables.KeepTogether(
                [Paragraph('%s/%s' % (index + 1, len(items)), styles['SlideNumber']), p]))
        
        first_template = PageTemplate(id='First',
                                      frames=[column_frame(inch / 2), column_frame(width / 2 + 0.25 * inch)],
                                      pagesize=pagesize,
                                      onPage=prepare_first_page)
        later_template = PageTemplate(id='Later',
                                      frames=[column_frame(inch / 2), column_frame(width / 2 + 0.25 * inch)],
                                      pagesize=pagesize,
                                      onPage=prepare_later_page)
        
        doc = DocTemplate(response)
        doc.addPageTemplates([first_template, later_template])
        doc.build(content)

        return response
