import re

from django.db import models
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import random
from PIL import Image
import os
import uuid
from ipaddr import IPAddress, IPNetwork
from rooibos.util import unique_slug
from rooibos.data.models import Record
from rooibos.access.functions import \
    get_effective_permissions_and_restrictions, check_access
from . import multimedia

import logging

logger = logging.getLogger(__name__)


class Storage(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    system = models.CharField(max_length=50)
    base = models.CharField(
        max_length=1024,
        null=True,
        help_text="Absolute path to server directory containing files."
    )

    credential_id = models.CharField(max_length=100, null=True, blank=True)
    credential_key = models.CharField(max_length=100, null=True, blank=True)

    urlbase = models.CharField(
        max_length=1024,
        null=True,
        blank=True,
        verbose_name='URL base',
        help_text="URL at which stored file is available, e.g. through "
        "streaming. May contain %(filename)s placeholder, which will be "
        "replaced with the media url property."
    )
    deliverybase = models.CharField(
        db_column='serverbase',
        max_length=1024,
        null=True,
        blank=True,
        verbose_name='server base',
        help_text="Absolute path to server directory in which a temporary "
        "symlink to the actual file should be created when the file is "
        "requested e.g. for streaming."
    )

    # Create storage systems only once and hold on to them to increase
    # performace, especially for cloud based storage systems
    storage_systems = dict()

    class Meta:
        verbose_name_plural = 'storage'
        app_label = 'storage'

    def save(self, **kwargs):
        unique_slug(
            self,
            slug_source='title',
            slug_field='name',
            check_current_slug=kwargs.get('force_insert')
        )
        super(Storage, self).save(kwargs)

    def __str__(self):
        return self.name

    @property
    def storage_system(self):
        key = (self.system, self.base)
        if (
            key not in Storage.storage_systems and
            self.system in settings.STORAGE_SYSTEMS
        ):
            (modulename, classname) = \
                settings.STORAGE_SYSTEMS[self.system].rsplit('.', 1)
            module = __import__(modulename)
            for c in modulename.split('.')[1:]:
                module = getattr(module, c)
            try:
                classobj = getattr(module, classname)
                Storage.storage_systems[key] = classobj(
                    base=self.base, storage=self)
            except Exception:
                logger.exception(
                    "Could not initialize storage %s" % classname)
                return None
        return Storage.storage_systems.get(key)

    def get_absolute_url(self):
        return reverse('storage-manage-storage', args=(self.id, self.name))

    def get_absolute_media_url(self, media):
        storage = self.storage_system
        return storage and storage.get_absolute_media_url(media) or None

    def get_delivery_media_url(self, media):
        storage = self.storage_system
        url = None
        if hasattr(storage, 'get_delivery_media_url'):
            url = storage.get_delivery_media_url(media)
        return url or self.get_absolute_media_url(media)

    def get_absolute_file_path(self, media):
        storage = self.storage_system
        return storage and storage.get_absolute_file_path(media) or None

    def save_file(self, name, content):
        storage = self.storage_system
        return storage and storage.save(name, content) or None

    def load_file(self, media):
        storage = self.storage_system
        return storage and storage.load_file(media) or None

    def delete_file(self, name):
        storage = self.storage_system
        if storage:
            storage.delete(name)

    def file_exists(self, name):
        storage = self.storage_system
        return storage and storage.exists(name) or False

    def size(self, name):
        storage = self.storage_system
        return storage and storage.size(name) or None

    def get_derivative_storage_path(self):
        sp = os.path.join(settings.SCRATCH_DIR, self.name)
        if not os.path.exists(sp):
            try:
                os.makedirs(sp)
            except:
                # check if directory exists now, if so another process
                # may have created it
                if not os.path.exists(sp):
                    # still does not exist, raise error
                    raise
        return sp

    def clear_derivative_storage_path(self):
        sp = self.get_derivative_storage_path()
        for f in os.listdir(sp):
            try:
                os.remove(os.path.join(sp, f))
            except:
                pass

    def clear_derivative_storage_for_media(self, media_id):
        path = self.get_derivative_storage_path()
        pattern = re.compile(r'^(tmp)?%d-' % media_id)
        count = 0
        for name in os.listdir(path):
            if pattern.match(name):
                try:
                    os.remove(os.path.join(path,  name))
                    count += 1
                except:
                    pass
        logger.debug('Cleared %d derivatives for media %d' % (count, media_id))

    def is_local(self):
        return self.storage_system and self.storage_system.is_local()

    def get_files(self):
        storage = self.storage_system
        if storage and hasattr(storage, 'get_files'):
            return storage.get_files()
        else:
            return []

    def get_upload_limit(self, user):
        if user.is_superuser:
            return 0
        r, w, m, restrictions = get_effective_permissions_and_restrictions(
            user, self)
        if restrictions:
            try:
                return int(restrictions['uploadlimit'])
            except (ValueError, KeyError):
                pass
        return getattr(settings, 'UPLOAD_LIMIT', 0)


class Media(models.Model):
    record = models.ForeignKey(Record)
    name = models.SlugField(max_length=50)
    url = models.CharField(max_length=1024)
    storage = models.ForeignKey(Storage)
    mimetype = models.CharField(max_length=128, default='application/binary')
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    bitrate = models.IntegerField(null=True)

    class Meta:
        unique_together = ("record", "name")
        verbose_name_plural = "media"
        app_label = 'storage'

    def __str__(self):
        return self.url

    def __repr__(self):
        return '<Media %r: %r %r %r %r>' % (
            self.id, self.record, self.storage, self.mimetype, self.url
        )

    def save(self, force_update_name=False, **kwargs):
        if self.url:
            slug_literal = os.path.splitext(os.path.basename(self.url))[0]
        else:
            slug_literal = "m-%s" % random.randint(1000000, 9999999)
        unique_slug(
            self,
            slug_literal=slug_literal,
            slug_field='name',
            check_current_slug=kwargs.get('force_insert') or force_update_name
        )
        super(Media, self).save(kwargs)

    def get_absolute_url(self):
        if self.storage:
            return self.storage.get_absolute_media_url(self)
        else:
            return self.url

    def get_delivery_url(self):
        if self.storage:
            return self.storage.get_delivery_media_url(self)
        else:
            return self.url

    def get_absolute_file_path(self):
        if self.storage:
            return self.storage.get_absolute_file_path(self)
        else:
            return None

    def save_file(self, name, content):
        if not hasattr(content, 'name'):
            content.name = name
        if not hasattr(content, 'mode'):
            content.mode = 'r'
        if not hasattr(content, 'size') and hasattr(content, 'len'):
            content.size = content.len
        if not isinstance(content, File):
            content = File(content)
        if self.storage:
            if self.id:
                self.storage.clear_derivative_storage_for_media(self.id)
            name = self.storage.save_file(name, content)
        else:
            name = None
        if name:
            self.url = name
            self.identify(save=False)
            self.name = os.path.splitext(os.path.basename(name))[0]
            self.save(force_update_name=True)
        else:
            raise IOError("Media file could not be stored")

    def load_file(self):
        return self.storage and self.storage.load_file(self) or None

    def file_exists(self):
        return self.storage and self.storage.file_exists(self.url) or False

    @property
    def file_size(self):
        if self.file_exists():
            return self.storage.size(self.url)
        else:
            return None

    def delete_file(self):
        if self.storage and self.url:
            if self.id:
                self.storage.clear_derivative_storage_for_media(self.id)
            return self.storage.storage_system.delete(self.url)
        else:
            return False

    def identify(self, save=True, lazy=False):
        if lazy and (self.width or self.height or self.bitrate):
            return
        type = self.mimetype.split('/')[0]
        if type == 'image':
            try:
                im = Image.open(self.get_absolute_file_path())
                (self.width, self.height) = im.size
            except:
                self.width = None
                self.height = None
            if save:
                self.save()
        elif type in ('video', 'audio'):
            width, height, bitrate = multimedia.identify(
                self.get_absolute_file_path())
            self.width = width
            self.height = height
            self.bitrate = bitrate
            if save:
                self.save()

    def is_local(self):
        return self.storage and self.storage.is_local()

    def is_downloadable_by(self, user, original=True):
        r, w, m, restrictions = get_effective_permissions_and_restrictions(
            user, self.storage)
        # if size or download restrictions exist, no direct download of a
        # media file is allowed
        if (restrictions and
                ((original and 'width' in restrictions) or
                 (original and 'height' in restrictions) or
                 restrictions.get('download', 'yes') == 'no')):
            return False
        else:
            return r

    def editable_by(self, user):
        return self.record.editable_by(user) and check_access(
            user, self.storage, write=True)

    def extract_text(self):
        if self.mimetype == 'text/plain':
            return self.load_file().read()
        elif self.mimetype == 'application/pdf':
            from .functions import extract_text_from_pdf_stream
            return extract_text_from_pdf_stream(self.load_file())
        else:
            return ''


class TrustedSubnet(models.Model):
    subnet = models.CharField(max_length=80)

    class Meta:
        app_label = 'storage'

    def __str__(self):
        return "TrustedSubnet (%s)" % self.subnet


class ProxyUrl(models.Model):
    uuid = models.CharField(max_length=36, unique=True)
    subnet = models.ForeignKey(TrustedSubnet)
    url = models.CharField(max_length=1024)
    context = models.CharField(max_length=256, null=True, blank=True)
    user = models.ForeignKey(User)
    user_backend = models.CharField(max_length=256, null=True, blank=True)
    last_access = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'storage'

    def __str__(self):
        return 'ProxyUrl %s: %s (Ctx %s, Usr %s, Sbn %s)' % (
            self.uuid, self.url, self.context, self.user, self.subnet)

    def get_absolute_url(self):
        return reverse('storage-proxyurl', kwargs=dict(uuid=self.uuid))

    @staticmethod
    def create_proxy_url(url, context, ip, user):
        ip = IPAddress(ip)
        for subnet in TrustedSubnet.objects.all():
            if ip in IPNetwork(subnet.subnet):
                break
        else:
            return None
        if hasattr(user, 'backend'):
            backend = user.backend
        else:
            backend = None
        proxy_url, created = ProxyUrl.objects.get_or_create(
            subnet=subnet,
            url=url,
            context=context,
            user=user,
            user_backend=backend,
            defaults=dict(uuid=str(uuid.uuid4()))
        )
        return proxy_url

    def get_additional_url(self, url):
        proxy_url, created = ProxyUrl.objects.get_or_create(
            subnet=self.subnet,
            url=url,
            context=self.context,
            user=self.user,
            user_backend=self.user_backend,
            defaults=dict(uuid=str(uuid.uuid4()))
        )
        return proxy_url
