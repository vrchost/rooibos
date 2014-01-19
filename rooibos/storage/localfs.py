from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.conf import settings
import os
import random
from time import time
import hashlib
from rooibos.util import create_link
from rooibos.statistics.models import Activity


class LocalFileSystemStorageSystem(FileSystemStorage):

    def __init__(self, base=None):
        FileSystemStorage.__init__(self, location=base, base_url=None)

    def get_absolute_media_url(self, storage, media):
        return reverse('storage-retrieve', kwargs={'recordid': media.record.id,
                                                   'record': media.record.name,
                                                   'mediaid': media.id,
                                                   'media': media.name})

    def get_delivery_media_url(self, storage, media):
        if storage.deliverybase and storage.urlbase:
            # Create a temporary symlink with an unguessable name to the actual file and return a link to that
            name = os.path.split(media.url)[1]
            # expiration is current time plus four hours rounded down to closest five minute interval
            # so that calling this method several times in a short timeframe should return the same name
            valid_until = hex((int(time() + 4 * 3600) / 300) * 300)[2:]  # cut off 0x prefix
            code = hashlib.md5(valid_until + name + settings.SECRET_KEY[:10]).hexdigest()[:16]
            filename = '-'.join([valid_until, code, name])
            symlink = os.path.join(storage.deliverybase, filename)
            if not os.path.exists(symlink):
                create_link(self.get_absolute_file_path(storage, media), symlink,
                            hard=getattr(settings, 'HARD_VIDEO_DELIVERY_LINKS', False))

            Activity.objects.create(event='media-delivery-url',
                    content_object=media,
                    data=dict(symlink=symlink))

            return storage.urlbase % dict(filename=filename)
        elif storage.urlbase:
            # Return a link based on the configured urlbase
            Activity.objects.create(event='media-delivery-url',
                    content_object=media)

            return storage.urlbase % dict(filename=media.url)
        else:
            # No special delivery options configured
            return None

    def get_absolute_file_path(self, storage, media):
        return self.path(media.url)

    def get_available_name(self, name):
        (name, ext) = os.path.splitext(name)
        unique = ""
        while True:
            if not self.exists(name + unique + ext):
                name = name + unique + ext
                break
            unique = "-1" if not unique else str(int(unique) - 1)
        return name

    def save(self, name, content):
        #todo need to create unique name, not random
        name = name or self.get_available_name("file-%s" % random.randint(1000000, 9999999))
        return FileSystemStorage.save(self, name, content)

    def is_local(self):
        return True

    def get_files(self):
        result = []
        location = os.path.normpath(self.location)
        for path, dirs, files in os.walk(location):
            path = path[len(location):]
            if path.startswith(os.path.sep):
                path = path[len(os.path.sep):]
            result.extend(os.path.normcase(os.path.join(path, file)) for file in files)
        return result
