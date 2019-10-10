"""
Storage system to store media files in Amazon S3
"""


from django.core.urlresolvers import reverse
from django.conf import settings
from storages.backends.s3boto import S3BotoStorage
import os
import random
import shutil
import tempfile


class S3StorageSystem(S3BotoStorage):
    """
    Storage system to store media files in Rackspace's cloud files
    """
    # Disable abstract class warning
    # pylint: disable=W0223

    containers = dict()

    def __init__(self, base=None, storage=None):

        bucket = None
        if base.startswith('//'):
            bucket, base = base[2:].split('/', 1)

        self.base = base
        self.storage = storage
        access_key = getattr(settings, 'AWS_ACCESS_KEY', None)
        secret_key = getattr(settings, 'AWS_SECRET_KEY', None)
        self.location = base

        super(S3StorageSystem, self).__init__(
            location=self.location,
            access_key=access_key,
            secret_key=secret_key,
            bucket=bucket
        )

    def _normalize_name(self, name):
        # workaround for bug:
        # http://code.larlet.fr/django-storages/pull-request/75
        # /fix-s3botostoragelistdir-with-aws_location/diff
        name = super(S3StorageSystem, self)._normalize_name(name)
        return name.rstrip('/')

    def get_absolute_media_url(self, media):
        return reverse('storage-retrieve', kwargs={'recordid': media.record.id,
                                                   'record': media.record.name,
                                                   'mediaid': media.id,
                                                   'media': media.name})

    def _get_local_path(self, media):
        localpath = self.storage.get_derivative_storage_path()
        localname = '%s-local%s' % (media.id, os.path.splitext(media.url)[1])
        return os.path.join(localpath, localname)

    def _create_local_copy(self, media):
        with tempfile.NamedTemporaryFile(
            mode='wb',
            prefix='tmp%s-' % media.id,
            delete=False,
            dir=self.storage.get_derivative_storage_path()
        ) as localfile:
            tempname = localfile.name
            shutil.copyfileobj(
                self.open(media.url), localfile, 5 * 1024 * 1024)
        try:
            os.rename(tempname, self._get_local_path(media))
        except Exception:
            # target file already exists, so delete this copy
            # we must have downloaded the same file twice
            try:
                os.remove(tempname)
            except:
                pass

    def get_absolute_file_path(self, media):
        local = self._get_local_path(media)
        if not os.path.exists(local):
            self._create_local_copy(media)
        return local

    def get_available_name(self, name, max_length):
        (name, ext) = os.path.splitext(name)
        unique = ""
        while True:
            if not self.exists(name + unique + ext):
                name = name + unique + ext
                break
            unique = "-1" if not unique else str(int(unique) - 1)
        return name

    def save(self, name, content):
        # TODO: need to create unique name, not random
        name = name or self.get_available_name(
            "file-%s" % random.randint(1000000, 9999999))
        return super(S3BotoStorage, self).save(name, content)

    def is_local(self):
        # Disable "could be a function" report
        # pylint: disable=R0201
        return True

    def get_files(self):
        result = self.listdir('')
        # remove empty string
        return [_f for _f in result[1] if _f]

    def load_file(self, media):
        localpath = self.get_absolute_file_path(media)
        return open(localpath, 'rb') if os.path.exists(localpath) else None
