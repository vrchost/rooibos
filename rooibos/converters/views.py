from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template import RequestContext
from rooibos.access import filter_by_access
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.solr import SolrIndex
from rooibos.solr.models import SolrIndexUpdates
from rooibos.storage.models import Storage, Media
from rooibos.presentation.models import Presentation, PresentationItem
import subprocess, re, os, sys, shutil
import logging
import tempfile


def convert_ppt(owner, title, collection, storage, tempdir, filename):
    # Call Open Office via the command line in order to convert Power Point Slides to Images
    cmd = '""%s" "%s" "%s" "%s" Width=1024 Format=2"' % (
        os.path.join(settings.OPEN_OFFICE_PATH, 'python'),
        os.path.join(settings.OPEN_OFFICE_PATH, 'DocumentConverter.py'),
        filename,
        filename + '.html',
    )
    logging.debug("Starting PowerPoint conversion: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.readlines():
        logging.error(line)
    p.wait()

    images = sorted(filter(lambda f: f.endswith('.jpg'), os.listdir(tempdir)), key=lambda i: int(i[3:-4]))
    if not images:
        return None

    dc = dict(
        title=Field.objects.get(name='title', standard__prefix='dc'),
        creator=Field.objects.get(name='creator', standard__prefix='dc'),
        source=Field.objects.get(name='source', standard__prefix='dc'),
    )

    presentation = Presentation.objects.create(owner=owner, title=title)
    for counter, image in enumerate(images):
        record = Record.objects.create(owner=owner)
        record.fieldvalue_set.create(field=dc['title'], value='Slide %s' % (counter + 1), order=1)
        record.fieldvalue_set.create(field=dc['source'], value=title, order=2)
        record.fieldvalue_set.create(field=dc['creator'], value=owner.get_full_name(), order=3)
        CollectionItem.objects.create(record=record, collection=collection)

        name = 'ppt-import-%s-%s-%s.jpg' % (owner.username, presentation.name, counter + 1)
        file = open(os.path.join(tempdir, image), 'rb')
        media = Media.objects.create(name=name, record=record, storage=storage, mimetype='image/jpeg')
        media.save_file(name=name, content=file)
        file.close()

        PresentationItem.objects.create(presentation=presentation, record=record, order=counter)

    return presentation


@login_required
def powerpoint(request):

    available_storage = get_list_or_404(filter_by_access(request.user, Storage, write=True).order_by('title').values_list('id', 'title'))
    available_collections = get_list_or_404(filter_by_access(request.user, Collection, write=True).order_by('title').values_list('id', 'title'))

    class UploadFileForm(forms.Form):
        title = forms.CharField(max_length=50)
        storage = forms.ChoiceField(choices=available_storage)
        collection = forms.ChoiceField(choices=available_collections)
        file = forms.FileField()

        def clean_file(self):
            file = self.cleaned_data['file']
            if not file.content_type in ('application/vnd.ms-powerpoint',
                                         'application/vnd.openxmlformats-officedocument.presentationml.presentation'):
                raise forms.ValidationError("The selected file does not appear to be a PowerPoint file")
            return file


    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            tempdir = tempfile.mkdtemp()
            infile = form.cleaned_data['file']
            filename = os.path.join(tempdir, 'a.ppt' if infile.content_type == 'application/vnd.ms-powerpoint' else 'a.pptx')
            outfile = open(filename, "wb+")
            for chunk in infile.chunks():
                outfile.write(chunk)
            outfile.close()
            presentation = convert_ppt(request.user,
                form.cleaned_data['title'],
                filter_by_access(request.user, Collection, write=True).get(id=form.cleaned_data['collection']),
                filter_by_access(request.user, Storage, write=True).get(id=form.cleaned_data['storage']),
                tempdir,
                filename)
            shutil.rmtree(tempdir)
            if not presentation:
                request.user.message_set.create(message="An error occurred while importing the presentation.")
            else:
                request.user.message_set.create(message="Presentation created successfully.")
                return HttpResponseRedirect(reverse('presentation-edit',
                                                    kwargs=dict(id=presentation.id, name=presentation.name)))
    else:
        form = UploadFileForm()
    return render_to_response('powerpoint.html',
                              {'form': form},
                              context_instance=RequestContext(request))
