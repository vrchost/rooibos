from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from backends.rackspace import CloudFilesStorage
import os
import random

class CloudFilesStorageSystem(CloudFilesStorage):

    def __init__(self, base=None):
        super(CloudFilesStorageSystem, self).__init__(container=base)

    def get_absolute_media_url(self, storage, media):
        return reverse('storage-retrieve', kwargs={'recordid': media.record.id,
                                                   'record': media.record.name,
                                                   'mediaid': media.id,
                                                   'media': media.name})

    def _create_local_copy(self, storage, media, derivative=None):
        m = derivative or Media.objects.create(record=media.record,
                                               storage=storage.get_derivative_storage(),
                                               mimetype=media.mimetype,
                                               master=media,
                                               name='-local-copy')
        m.save_file('%s-local-copy' + os.path.splitext(media.url)[1], media.load_file())

    def get_absolute_file_path(self, storage, media):
        try:
            m = media.derivatives.get(name='-local-copy')
            if not m.file_exists():
                m = self._create_local_copy(storage, media, derivative=m)
        except Media.DoesNotExist:
            m = self._create_local_copy(storage, media)
        except Exception, ex:
            print ex
        return m.get_absolute_file_path()

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
        return super(CloudFilesStorageSystem, self).save(name, content)

    def is_local(self):
        return False
    
