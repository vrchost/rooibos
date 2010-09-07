from __future__ import with_statement
from zipfile import ZipFile, ZIP_DEFLATED
import os
import xml.dom.minidom
from tempfile import mkstemp
from django.core.urlresolvers import reverse
from django.conf.urls.defaults import url
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.access import filter_by_access
from rooibos.data.models import Collection
from rooibos.util import guess_extension
from rooibos.storage import get_image_for_record
from rooibos.storage.models import Media
from rooibos.presentation.models import Presentation


PROCESS_FILES = {
    'ppt/slides/_rels/slide2.xml.rels': 'record_slide_rels',
    'ppt/slides/slide1.xml': 'title_slide',
    'ppt/slides/slide2.xml': 'record_slide',
    'ppt/notesSlides/notesSlide1.xml': 'title_slide_notes',
    'ppt/notesSlides/notesSlide2.xml': 'record_slide_notes',
    'ppt/notesSlides/_rels/notesSlide2.xml.rels': 'record_slide_notes_rels',
    'ppt/presentation.xml': 'presentation',
    'ppt/_rels/presentation.xml.rels': 'presentation_rels',
    '[Content_Types].xml': 'content_types',   
}


class PowerPointGenerator:
    
    def __init__(self, presentation, user):        
        self.presentation = presentation
        self.items = presentation.items.filter(hidden=False)
        self.slide_template = None
        self.slide_rel_template = None
        self.slide_notes_template = None
        self.slide_notes_rel_template = None
        self.content_types = None
        self.additional_content_types = {}
        self.placeholder_image = None
        self.remove_placeholder_image = True
        self.media = {}
        self.user = user
        
    @staticmethod
    def get_templates():
        return filter(lambda f: f.endswith('.pptx'), os.listdir(os.path.join(os.path.dirname(__file__), 'pptx_templates')))
    
    def generate(self, template, outfile):
        if len(self.items) == 0:
            return False
        template = ZipFile(os.path.join(os.path.dirname(__file__), 'pptx_templates', template), mode='r')
        outfile = ZipFile(outfile, mode='w', compression=ZIP_DEFLATED)
        for name in template.namelist():
            content = template.read(name)
            if PROCESS_FILES.has_key(name):
                p = getattr(self, '_' + PROCESS_FILES[name])
                p(name, content, outfile)
            else:
                if name.startswith('ppt/media/'):
                    self.media[name] = content
                else:
                    outfile.writestr(name, content)
        template.close()
        self._process_slides(outfile)
        self._process_content_types(outfile)
        for name in self.media:
            if name != self.placeholder_image or not self.remove_placeholder_image:
                outfile.writestr(name, self.media[name])
        outfile.close()        
        return True
                
    def _process_slides(self, outfile):
        for n in range(2, len(self.items) + 2):
            item = self.items[n - 2]
            
            x = xml.dom.minidom.parseString(self.slide_template)
            xr = xml.dom.minidom.parseString(self.slide_rel_template)
            xn = xml.dom.minidom.parseString(self.slide_notes_template)
            xnr = xml.dom.minidom.parseString(self.slide_notes_rel_template)
            record = item.record

            # insert notes
            fieldvalues = list(item.get_fieldvalues())
            if fieldvalues:
                fieldvalues[0]._subitem = False
            for i in range(1, len(fieldvalues)):
                fieldvalues[i]._subitem = (fieldvalues[i].field == fieldvalues[i - 1].field and
                                          fieldvalues[i].group == fieldvalues[i - 1].group)                
                
            body = xn.getElementsByTagName('p:txBody').item(0)
            
            def appendText(text):
                ap1 = xn.createElement('a:p')
                ar = xn.createElement('a:r') 
                arPr = xn.createElement('a:rPr')
                arPr.setAttribute('dirty','0') 
                arPr.setAttribute('lang','en-US') 
                arPr.setAttribute('smtClean','0')
                at = xn.createElement('a:t')
                txt = xn.createTextNode(text)
                at.appendChild(txt) 
                ar.appendChild(arPr)
                ar.appendChild(at)
                ap1.appendChild(ar)
                body.appendChild(ap1)
            
            for value in fieldvalues:
                appendText('%s%s: %s' % (
                      value._subitem and 'sub' or '', 
                      value.resolved_label, 
                      value.value or ''))

            annotation = item.annotation
            if annotation:
                appendText('Annotation: %s' % annotation)
            
            test = xn.toxml(encoding="UTF-8")
            
            # update the slide number in notes
            e = filter(lambda e: e.getAttribute('type') == 'slidenum', xn.getElementsByTagName('a:fld'))[0]
            e.getElementsByTagName('a:t').item(0).firstChild.nodeValue = n
            
            # insert title
            for e in x.getElementsByTagName('a:t'):
                t = e.firstChild.nodeValue
                if t == 'title':
                    t = item.title or ''
                e.firstChild.nodeValue = t
            # insert image if available
            image = get_image_for_record(record, self.user, 800, 600)
            if image:                
                # add image to outfile
                f = image.load_file()
                if f:
                    ext = guess_extension(image.mimetype)
                    name = 'rooibos%s%s' % (n, ext)
                    self.additional_content_types.setdefault(image.mimetype, ext[1:])
                    outfile.writestr('ppt/media/' + name, f.read())
                    
                    # find image placeholder
                    e = filter(lambda e: e.getAttribute('descr') == 'image', x.getElementsByTagName('p:cNvPr'))[0]
                    e = e.parentNode.parentNode
                    embedId = e.getElementsByTagName('a:blip')[0].getAttribute('r:embed')
                    
                    if image.width and image.height:                        
                        offset = e.getElementsByTagName('a:off')[0]
                        extent = e.getElementsByTagName('a:ext')[0]
                        px = int(offset.getAttribute('x'))
                        py = int(offset.getAttribute('y'))
                        pw = int(extent.getAttribute('cx'))
                        ph = int(extent.getAttribute('cy'))
                        
                        imageratio = image.width * 1.0 / image.height
                        ratio = pw * 1.0 / ph
                        
                        if imageratio > ratio:
                            new_h = image.height * pw / image.width
                            new_w = pw
                            new_x = px
                            new_y = py + (ph - new_h) / 2
                        else:
                            new_h = ph
                            new_w = image.width * ph / image.height
                            new_x = px + (pw - new_w) / 2
                            new_y = py
                    
                        offset.setAttribute('x', str(new_x))
                        offset.setAttribute('y', str(new_y))
                        extent.setAttribute('cx', str(new_w))
                        extent.setAttribute('cy', str(new_h))
                    
                    # add image to slide relation
                    rel = filter(lambda e: e.getAttribute('Id') == embedId, xr.getElementsByTagName('Relationship'))[0]
                    self.placeholder_image = 'ppt' + rel.getAttribute('Target')[2:]
                    rel.setAttribute('Target', '../media/' + name)
                    
                    # add notes to slide relation
                    rel2 = filter(lambda e: e.getAttribute('Type') == 
                                  "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide", 
                                  xr.getElementsByTagName('Relationship'))[0]
                    rel2.setAttribute('Target', '../notesSlides/notesSlide%s.xml' % n)
                    
                    # add slide to notes relation
                    rel3 = filter(lambda e: e.getAttribute('Type') == 
                                  "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", 
                                  xnr.getElementsByTagName('Relationship'))[0]
                    rel3.setAttribute('Target', '../slides/slide%s.xml' % n)
            else:
                self.remove_placeholder_image = False
            
            outfile.writestr('ppt/slides/slide%s.xml' % n, x.toxml(encoding="UTF-8"))     
            outfile.writestr('ppt/slides/_rels/slide%s.xml.rels' % n, xr.toxml())     
            outfile.writestr('ppt/notesSlides/notesSlide%s.xml' % n, xn.toxml(encoding="UTF-8"))     
            outfile.writestr('ppt/notesSlides/_rels/notesSlide%s.xml.rels' % n, xnr.toxml())     
    
    def _process_content_types(self, outfile):
        x = xml.dom.minidom.parseString(self.content_types)
        for n in range(3, len(self.items) + 2):
            e = x.createElement('Override')
            e.setAttribute('PartName', '/ppt/slides/slide%s.xml' % n)
            e.setAttribute('ContentType', 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
            x.firstChild.appendChild(e)
            e = x.createElement('Override')
            e.setAttribute('PartName', '/ppt/notesSlides/notesSlide%s.xml' % n)
            e.setAttribute('ContentType', 'application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml')
            x.firstChild.appendChild(e)
        for e in x.getElementsByTagName('Default'):
            # remove additional content types that already exist
            self.additional_content_types.pop(e.getAttribute('ContentType'), None)
        for c in self.additional_content_types:
            e = x.createElement('Default')
            e.setAttribute('ContentType', c)
            e.setAttribute('Extension', self.additional_content_types[c])
            x.firstChild.appendChild(e)
        outfile.writestr('[Content_Types].xml', x.toxml())
    
    def _title_slide(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        for e in x.getElementsByTagName('a:t'):
            t = e.firstChild.nodeValue
            if t == 'title':
                t = self.presentation.title
            elif t == 'description':
                t = self.presentation.description or ''
            e.firstChild.nodeValue = t        
        outfile.writestr(name, x.toxml())        
        
    def _record_slide(self, name, content, outfile):
        self.slide_template = content
        
    def _record_slide_rels(self, name, content, outfile):
        self.slide_rel_template = content

    def _record_slide_notes(self, name, content, outfile):
        self.slide_notes_template = content

    def _title_slide_notes(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        outfile.writestr(name, x.toxml())        

    def _record_slide_notes_rels(self, name, content, outfile):
        self.slide_notes_rel_template = content

    def _presentation(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        p = x.getElementsByTagName('p:sldIdLst')[0]
        maxid = max(map(lambda e: int(e.getAttribute('id')), p.getElementsByTagName('p:sldId')))
        for n in range(3, len(self.items) + 2):
            e = x.createElement('p:sldId')
            e.setAttribute('id', str(maxid + n))
            e.setAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships', 'r:id', 'rooibosId%s' % n)
            p.appendChild(e)
        outfile.writestr(name, x.toxml())
    
    def _presentation_rels(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        p = x.getElementsByTagName('Relationships')[0]
        for n in range(3, len(self.items) + 2):
            e = x.createElement('Relationship')
            e.setAttribute('Id', 'rooibosId%s' % n)
            e.setAttribute('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide')
            e.setAttribute('Target', 'slides/slide%s.xml' % n)
            p.appendChild(e)
        outfile.writestr(name, x.toxml())
    
    def _content_types(self, name, content, outfile):
        self.content_types = content
    

class PowerPointPresentation(object):

    title = "PowerPoint"
    weight = 20
    
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
        return [url(r'^powerpoint/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.options, name='viewers-powerpoint'),
                url(r'^powerpoint/(?P<id>[\d]+)/(?P<name>[-\w]+)/(?P<template>[^/]+)/$', self.generate, name='viewers-powerpoint-download'),
                url(r'^powerpoint/(?P<template>[^/]+)/thumb/$', self.thumbnail, name='viewers-powerpoint-thumbnail')]
    
    def url_for_obj(self, obj):
        return reverse('viewers-powerpoint', kwargs={'id': obj.id, 'name': obj.name})
    
    def options(self, request, id, name):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        presentation = Presentation.get_by_id_for_request(id, request)
        if not presentation:
            return HttpResponseRedirect(return_url)

        templates = [(reverse('viewers-powerpoint-download', kwargs={'id': presentation.id,
                                                                        'name': presentation.name,
                                                                        'template': t}),
                      reverse('viewers-powerpoint-thumbnail', kwargs={'template': t}),
                      t[:-5].capitalize())
                         for t in PowerPointGenerator.get_templates()]
        return render_to_response('presentations/powerpoint/options.html',
                                  {'templates': templates,
                                   'presentation': presentation,
                                   'next': return_url,
                                   },
                                  context_instance=RequestContext(request))
    
    def generate(self, request, id, name, template):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        presentation = Presentation.get_by_id_for_request(id, request)
        if not presentation:
            return HttpResponseRedirect(return_url)
            
        g = PowerPointGenerator(presentation, request.user)
        filename = os.tempnam()
        try:
            g.generate(template, filename)
            with open(filename, mode="rb") as f:
                response = HttpResponse(content=f.read(),
                    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
            response['Content-Disposition'] = 'attachment; filename=%s.pptx' % name
            return response        
        finally:
            try:
                os.unlink(filename)
            except:
                pass
    
    def thumbnail(self, request, template):
        filename = os.path.join(os.path.dirname(__file__), 'pptx_templates', template)
        if not os.path.isfile(filename):
            raise Http404()
        template = ZipFile(filename, mode='r')
        return HttpResponse(content=template.read('docProps/thumbnail.jpeg'), mimetype='image/jpg')
