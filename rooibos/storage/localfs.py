from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
import os
import random

class LocalFileSystemStorageSystem(FileSystemStorage):

    def __init__(self, base=None):
        FileSystemStorage.__init__(self, location=base, base_url=None)

    def get_absolute_media_url(self, storage, media):
        return reverse('storage-retrieve', kwargs={'recordid': media.record.id,
                                                   'record': media.record.name,
                                                   'mediaid': media.id,
                                                   'media': media.name})

    def get_delivery_media_url(self, storage, media):
        if storage.urlbase:
            return storage.urlbase % dict(filename=media.url)
        else:
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
            result.extend(os.path.join(path, file) for file in files)
        return result
