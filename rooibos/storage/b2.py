"""
Storage system to store media files in Backblaze B2
"""


from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from b2sdk.account_info.sqlite_account_info import SqliteAccountInfo
from b2sdk.api import B2Api
from b2sdk.download_dest import DownloadDestLocalFile

import re
import os
import random
import shutil
import tempfile
import mimetypes


class LocalFileSystemStorageSystem(FileSystemStorage):

    def __init__(self, base, storage):
        FileSystemStorage.__init__(self, location=base, base_url=None)
        self.storage = storage


class B2StorageSystem(FileSystemStorage):

    def __init__(self, base=None, storage=None):

        super(B2StorageSystem, self).__init__(location=base, base_url=None)

        self.base = base
        self.storage = storage

        match = re.match(r'^(b2:)?(//)?(\w+)/(.+)/?$', base)
        if not match:
            return

        bucket = match.group(3)
        self.path = match.group(4)

        file_name = os.path.expanduser('~/.b2_account_info-%d' % storage.id)
        self.api = B2Api(SqliteAccountInfo(file_name=file_name))
        self.api.authorize_account(
            'production',
            storage.credential_id,
            storage.credential_key,
        )
        self.bucket = self.api.get_bucket_by_name(bucket)

    def _normalize_name(self, name):
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
            self.bucket.download_file_by_name(
                self.path + '/' + media.url,
                DownloadDestLocalFile(tempname),
            )
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

    def exists(self, name):
        name = self.path + '/' + name
        result = self.bucket.list_file_names(name, 1)
        return len(result['files']) and result['files'][0]['fileName'] == name

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
        name = '%s/%s' % (self.path, name)
        mime_type = mimetypes.guess_type(name)[0]
        return self.bucket.upload_bytes(
            content, name, content_type=mime_type)

    def is_local(self):
        # Disable "could be a function" report
        # pylint: disable=R0201
        return True

    def get_files(self):
        return list(
            f[0].file_name.split('/')[-1]
            for f in self.bucket.ls(self.path)
            if not f[1]  # filter our subdirs
        )

    def load_file(self, media):
        localpath = self.get_absolute_file_path(media)
        return open(localpath, 'rb') if os.path.exists(localpath) else None
