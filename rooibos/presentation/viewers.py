from django import forms
from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.files.temp import NamedTemporaryFile
from django.core.servers.basehttp import FileWrapper
from django.template import Context, Template
from django.utils.encoding import smart_str, smart_unicode
from rooibos.access import get_effective_permissions_and_restrictions, filter_by_access
from rooibos.viewers import register_viewer, Viewer
from rooibos.storage import get_image_for_record
from rooibos.data.models import Record, Collection
from rooibos.api.views import presentation_detail
from models import Presentation
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.colors import white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import flowables
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import BaseDocTemplate, PageTemplate
from PIL import Image
import re
import math
import zipfile
import os
from StringIO import StringIO


def _get_presentation(obj, request, objid):
    if obj:
        if not isinstance(obj, Presentation):
            return None
    else:
        obj = Presentation.get_by_id_for_request(objid, request)
        if not obj:
            return None
    return obj


class PresentationViewer(Viewer):

    title = "View"
    weight = 100

    def view(self, request):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        return render_to_response('presentation_viewer.html',
                                  {'presentation': self.obj,
                                   'return_url': return_url,
                                },
                            context_instance=RequestContext(request))


@register_viewer('presentationviewer', PresentationViewer)
def presentationviewer(obj, request, objid=None):
    presentation = _get_presentation(obj, request, objid)
    return PresentationViewer(presentation, request.user) if presentation else None



class FlashCardViewer(Viewer):

    title = "Flash Cards"
    weight = 18

    def view(self, request):
        presentation = self.obj

        passwords = request.session.get('passwords', dict())

        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'filename="' + presentation.title + '-flashCards.pdf"'

        pagesize = getattr(pagesizes, settings.PDF_PAGESIZE)
        width, height = pagesize

        p = canvas.Canvas(response, pagesize=pagesize)

        def getStyleSheet():
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

        def getParagraph(*args, **kwargs):
            try:
                return Paragraph(*args, **kwargs)
            except (AttributeError, IndexError):
                return None

        def drawCard(index, item):
            p.saveState()
            p.translate(0, height / 3 * (2 - index % 3))

            # retrieve record while making sure it's accessible to presentation owner
            record = Record.filter_one_by_access(presentation.owner, item.record.id)

            if record:
                image = get_image_for_record(record, presentation.owner, 800, 800, passwords)
                if image:
                    p.drawImage(image, inch / 2, inch / 2, width=width / 2 - inch, height=height / 3 - inch,
                                preserveAspectRatio=True)
                f = Frame(width / 2 + inch / 2, inch / 2,
                          width=width / 2 - inch, height = height / 3 - inch,
                          leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
                data = []
                data.append(getParagraph('%s/%s' % (index + 1, len(items)), styles['SlideNumber']))
                values = item.get_fieldvalues(owner=request.user)
                for value in values:
                    v = value.value if len(value.value) < 100 else value.value[:100] + '...'
                    data.append(getParagraph('<b>%s:</b> %s' % (value.resolved_label, v), styles['Data']))
                annotation = item.annotation
                if annotation:
                    data.append(getParagraph('<b>%s:</b> %s' % ('Annotation', annotation), styles['Data']))
                data = filter(None, data)
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


@register_viewer('flashcardviewer', FlashCardViewer)
def flashcardviewer(obj, request, objid=None):
    presentation = _get_presentation(obj, request, objid)
    return FlashCardViewer(presentation, request.user) if presentation else None



class PrintViewViewer(Viewer):

    title = "Print View"
    weight = 18

    def view(self, request):
        presentation = self.obj

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

        def getStyleSheet():
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
            try:
                p = Paragraph(''.join(text), styles['Normal'])
            except (AttributeError, KeyError, IndexError):
                # this sometimes triggers an error in reportlab
                p = None
            if p:
                image = get_image_for_record(item.record, presentation.owner, 100, 100, passwords)
                if image:
                    try:
                        i = flowables.Image(image, kind='proportional',
                                            width=1 * inch, height=1 * inch)
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

        response['Content-Disposition'] = 'filename="' + smart_str(presentation.title) + '.pdf"'

        return response


@register_viewer('printviewviewer', PrintViewViewer)
def printviewviewer(obj, request, objid=None):
    presentation = _get_presentation(obj, request, objid)
    return PrintViewViewer(presentation, request.user) if presentation else None



class PackageFilesViewer(Viewer):

    title = "Package Files"
    weight = 25

    def view(self, request):

        def filename(title):
            return re.sub('[^A-Za-z0-9_. ]+', '-', title)[:32]

        def write(output, image, index, title, prefix=None):
            if image:
                output.write(image, ('%s%s %s%s' % (
                    os.path.join(prefix, '') if prefix else '',
                    str(index + 1).zfill(4),
                    filename(title or 'Slide %s' % (index + 1)),
                    os.path.splitext(image)[1])
                    ).encode('ascii', 'replace'))

        def metadata_file(tempfile, record):
            t = Template("{% load data %}{% metadata record %}")
            c = Context({'record': record, 'request': request})
            tempfile.write(smart_str(t.render(c)))
            tempfile.flush()
            return tempfile.name

        presentation = self.obj
        passwords = request.session.get('passwords', dict())
        items = presentation.items.filter(hidden=False)

        tempfile = NamedTemporaryFile(suffix='.zip')
        output = zipfile.ZipFile(tempfile, 'w')

        tempjsonfile = NamedTemporaryFile(suffix='.json')
        metadata = presentation_detail(request, presentation.id)
        tempjsonfile.write(metadata.content)
        tempjsonfile.flush()
        output.write(tempjsonfile.name, os.path.join('metadata', 'metadata.json'))

        for index, item in enumerate(items):
            write(output, get_image_for_record(item.record, self.user, passwords=passwords),
                  index, item.record.title)
            write(output, get_image_for_record(item.record, self.user, 100, 100, passwords),
                  index, item.record.title, 'thumb')

            tempmetadatafile = NamedTemporaryFile(suffix='.html')
            write(output, metadata_file(tempmetadatafile, item.record),
                  index, item.record.title, 'metadata')

        output.close()
        tempfile.flush()
        tempfile.seek(0)

        wrapper = FileWrapper(tempfile)
        response = HttpResponse(wrapper, mimetype='application/zip')
        response['Content-Disposition'] = 'attachment; filename=%s.zip' % filename(presentation.title)
        response['Content-Length'] = os.path.getsize(tempfile.name)
        return response


@register_viewer('packagefilesviewer', PackageFilesViewer)
def packagefilesviewer(obj, request, objid=None):
    presentation = _get_presentation(obj, request, objid)
    return PackageFilesViewer(presentation, request.user) if presentation else None
