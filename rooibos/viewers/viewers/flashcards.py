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
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.frames import Frame
import Image


def getStyleSheet():
    """Returns a stylesheet object"""
    stylesheet = StyleSheet1()

    stylesheet.add(ParagraphStyle(name='Normal',
                                  fontName='Times-Roman',
                                  fontSize=8,
                                  leading=10))
    stylesheet.add(ParagraphStyle(name='SlideNumber',
                                  parent=stylesheet['Normal'],
                                  alignment=TA_RIGHT,
                                  fontSize=6,
                                  leading=8))
    stylesheet.add(ParagraphStyle(name='Data',
                                  parent=stylesheet['Normal'],
                                  leftIndent=18,
                                  firstLineIndent=-18,
                                  ))
    return stylesheet


class FlashCards(object):

    title = "Flash Cards"
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
        return url(r'^flashcards/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.view, name='viewers-flashcards')
    
    def url_for_obj(self, obj):
        return reverse('viewers-flashcards', kwargs={'id': obj.id, 'name': obj.name})
    
    def view(self, request, id, name):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        presentation = Presentation.get_by_id_for_request(id, request)
        if not presentation:
            return HttpResponseRedirect(return_url)

        passwords = request.session.get('passwords', dict())

        response = HttpResponse(mimetype='application/pdf')

        pagesize = getattr(pagesizes, settings.PDF_PAGESIZE)
        width, height = pagesize
        
        p = canvas.Canvas(response, pagesize=pagesize)
        styles = getStyleSheet()
        
        items = presentation.items.filter(hidden=False)
        
        def decoratePage():
            p.saveState()
            p.setDash(2, 2)
            p.setStrokeColorRGB(0.8, 0.8, 0.8)
            p.line(width / 2, inch / 2, width / 2, height - inch / 2)
            p.line(inch / 2, height / 3, width - inch / 2, height / 3)
            p.line(inch / 2, height / 3 * 2, width - inch / 2, height / 3 * 2)
            p.setFont('Helvetica', 8)
            p.setFillColorRGB(0.8, 0.8, 0.8)
            p.drawString(inch, height / 3 - 3 * inch / 72, 'Cut here')
            p.drawString(inch, height / 3 * 2 - 3 * inch / 72, 'Cut here')
            p.translate(width / 2 - 3 * inch / 72, height - inch)
            p.rotate(270)
            p.drawString(0, 0, 'Fold here')
            p.restoreState()
        
        def drawCard(index, item):
            p.saveState()
            p.translate(0, height / 3 * (2 - index % 3))
            
            try:
                # retrieve record while making sure it's accessible to presentation owner
                record = Record.objects.get(Q(owner=presentation.owner) |
                                            Q(collection__in=filter_by_access(presentation.owner, Collection)),
                                            id=item.record.id)
            except Record.DoesNotExist:
                record = None
                
            if record:
                image = get_image_for_record(record, presentation.owner, 800, 800, passwords, force_local=True)
                if image:
                    p.drawImage(image.get_absolute_file_path(), inch / 2, inch / 2, width=width / 2 - inch, height=height / 3 - inch)
                f = Frame(width / 2 + inch / 2, inch / 2,
                          width=width / 2 - inch, height = height / 3 - inch,
                          leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
                data = []
                data.append(Paragraph('%s/%s' % (index + 1, len(items)), styles['SlideNumber']))
                values = item.get_fieldvalues(owner=request.user)
                for value in values:
                    v = value.value if len(value.value) < 100 else value.value[:100] + '...'
                    data.append(Paragraph('<b>%s:</b> %s' % (value.resolved_label, v), styles['Data']))
                annotation = item.annotation
                if annotation:
                    data.append(Paragraph('<b>%s:</b> %s' % ('Annotation', annotation), styles['Data']))
                f.addFromList(data, p)
                if data:
                    p.setFont('Helvetica', 8)
                    p.setFillColorRGB(0, 0, 0)
                    p.drawRightString(width - inch / 2, inch / 2, '...')
            
            p.restoreState()
        
        for index, item in enumerate(items):
            if index % 3 == 0:
                if index > 0:
                    p.showPage()
                decoratePage()
            drawCard(index, item)
            
        p.showPage()        
        p.save()
        return response
