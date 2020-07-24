import json
import os
import re
import zipfile

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.files.temp import NamedTemporaryFile
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import loader
from wsgiref.util import FileWrapper

from rooibos.presentation.views import raw_manifest, transparent_png, \
    missing_png
from rooibos.storage.functions import get_image_for_record
from rooibos.viewers import Viewer


STATIC_FILES = [
    'mirador/css/mirador-combined.css',
    'presentation/viewer.css',
    'mirador/mirador.js',
    'presentation/viewer.js',
    'mirador/images/debut_dark.png',
    'mirador/locales/en-US/translation.json',
    'mirador/locales/en/translation.json',
    'mirador/fonts/fontawesome-webfont.woff2',
    'mirador/fonts/fontawesome-webfont.woff',
    'mirador/fonts/fontawesome-webfont.ttf',
    'mirador/fonts/MaterialIcons-Regular.woff2',
    'mirador/fonts/MaterialIcons-Regular.woff',
    'mirador/fonts/MaterialIcons-Regular.ttf',
]


class MiradorPackageViewer(Viewer):

    title = "Package Viewer"
    weight = 95

    def view(self, request):

        def filename(title):
            return re.sub('[^A-Za-z0-9_. ]+', '-', title)[:32]

        presentation = self.obj
        passwords = request.session.get('passwords', dict())
        items = presentation.items.filter(hidden=False)

        tempfile = NamedTemporaryFile(suffix='.zip')
        output = zipfile.ZipFile(tempfile, 'w')

        template_name = getattr(
            settings,
            'PRESENTATION_VIEWER_TEMPLATE',
            'presentation_viewer.html'
        )
        page = loader.render_to_string(template_name, {
            'presentation': self.obj,
            'return_url': '/exit',
            'manifest_url': '/presentation/manifest.json',
        })

        manifest = raw_manifest(request, self.obj.id, self.obj.name, offline=True)

        output.writestr('presentation/index.html', page)
        output.writestr('presentation/manifest.json', json.dumps(manifest))

        for static_file in STATIC_FILES:
            path = finders.find(static_file)
            if path:
                output.write(path, 'static/' + static_file)

        package_files_dir = os.path.join(
            os.path.dirname(__file__), 'mirador_package')
        for root, dirs, files in os.walk(package_files_dir):
            for f in files:
                path = os.path.join(root, f)
                output.write(path, os.path.relpath(path, package_files_dir))

        for item in items:
            image = get_image_for_record(
                    item.record, self.user, passwords=passwords)
            outpath = item.record.get_image_url(
                force_reprocess=False,
                handler='storage-retrieve-iiif-image',
            )
            if image:
                output.write(image, outpath)

            image = get_image_for_record(
                    item.record, self.user, 100, 100, passwords=passwords)
            if image:
                output.write(
                    image,
                    'thumbs' + outpath,
                )

        output.writestr(
            reverse('presentation-blank-slide', kwargs=dict(extra='')).strip('/'),
            transparent_png(request, None).content
        )
        output.writestr(
            reverse('presentation-missing-slide', kwargs=dict(extra='')).strip('/'),
            missing_png(request, None).content
        )

        output.close()
        tempfile.flush()
        tempfile.seek(0)
        size = os.path.getsize(tempfile.name)

        wrapper = FileWrapper(tempfile)
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = \
            'attachment; filename=%s.zip' % filename(presentation.title)
        response['Content-Length'] = size
        return response
