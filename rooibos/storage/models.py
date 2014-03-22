from django.db import models
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import random
from PIL import Image
import os
import uuid
from rooibos.contrib.ipaddr import IP
from rooibos.util import unique_slug
from rooibos.data.models import Record
from rooibos.access import sync_access, get_effective_permissions_and_restrictions, check_access
import multimedia
from functions import extractTextFromPdfStream

import logging


class Storage(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    system = models.CharField(max_length=50)
    base = models.CharField(max_length=1024, null=True,
                            help_text="Absolute path to server directory containing files.")
    urlbase = models.CharField(max_length=1024, null=True, blank=True, verbose_name='URL base',
                               help_text="URL at which stored file is available, e.g. through streaming. " +
                               "May contain %(filename)s placeholder, which will be replaced with the media url property.")
    deliverybase = models.CharField(db_column='serverbase', max_length=1024,
                                    null=True, blank=True, verbose_name='server base',
                                    help_text="Absolute path to server directory in which a temporary symlink " +
                                    "to the actual file should be created when the file is requested e.g. for " +
                                    "streaming.")
    # This field is no longer used
    #derivative = models.OneToOneField('self', null=True, related_name='master')
    derivative = models.IntegerField(null=True, db_column='derivative_id')

    class Meta:
        verbose_name_plural = 'storage'

    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Storage, self).save(kwargs)

    def __unicode__(self):
        return self.name

    @property
    def storage_system(self):
        if settings.STORAGE_SYSTEMS.has_key(self.system):
            (modulename, classname) = settings.STORAGE_SYSTEMS[self.system].rsplit('.', 1)
            module = __import__(modulename)
            for c in modulename.split('.')[1:]:
                module = getattr(module, c)
            classobj = getattr(module, classname)
            try:
                return classobj(base=self.base)
            except Exception:
                logging.exception("Could not initialize storage %s" % classname)
                return None
        else:
            return None

    def get_absolute_url(self):
        return reverse('storage-manage-storage', args=(self.id, self.name))

    def get_absolute_media_url(self, media):
        storage = self.storage_system
        return storage and storage.get_absolute_media_url(self, media) or None

    def get_delivery_media_url(self, media):
        storage = self.storage_system
        url = None
        if hasattr(storage, 'get_delivery_media_url'):
            url = storage.get_delivery_media_url(self, media)
        return url or self.get_absolute_media_url(media)

    def get_absolute_file_path(self, media):
        storage = self.storage_system
        return storage and storage.get_absolute_file_path(self, media) or None

    def save_file(self, name, content):
        storage = self.storage_system
        return storage and storage.save(name, content) or None

    def load_file(self, name):
        storage = self.storage_system
        return storage and storage.open(name) or None

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
                # check if directory exists now, if so another process may have created it
                if not os.path.exists(sp):
                    # still does not exist, raise error
                    raise
        return sp

    def is_local(self):
        return self.storage_system and self.storage_system.is_local()

    def get_files(self):
        storage = self.storage_system
        return storage.get_files() if storage and hasattr(storage, 'get_files') else []

    def get_upload_limit(self, user):
        if user.is_superuser:
            return 0
        r, w, m, restrictions = get_effective_permissions_and_restrictions(user, self)
        if restrictions:
            try:
                return int(restrictions['uploadlimit'])
            except (ValueError, KeyError):
                pass
        return settings.UPLOAD_LIMIT


class Media(models.Model):
    record = models.ForeignKey(Record)
    name = models.SlugField(max_length=50)
    url = models.CharField(max_length=1024)
    storage = models.ForeignKey(Storage)
    mimetype = models.CharField(max_length=128, default='application/binary')
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    bitrate = models.IntegerField(null=True)
    # This field is no longer used
    master = models.ForeignKey('self', null=True, related_name='derivatives')

    class Meta:
        unique_together = ("record", "name")
        verbose_name_plural = "media"

    def __unicode__(self):
        return self.url

    def save(self, force_update_name=False, **kwargs):
        unique_slug(self, slug_literal=os.path.splitext(os.path.basename(self.url))[0] if self.url else "m-%s" % random.randint(1000000, 9999999),
                    slug_field='name', check_current_slug=kwargs.get('force_insert') or force_update_name)
        super(Media, self).save(kwargs)

    def get_absolute_url(self):
        return self.storage and self.storage.get_absolute_media_url(self) or self.url

    def get_delivery_url(self):
        return self.storage and self.storage.get_delivery_media_url(self) or self.url

    def get_absolute_file_path(self):
        return self.storage and self.storage.get_absolute_file_path(self) or None

    def save_file(self, name, content):
        if not hasattr(content, 'name'):
            content.name = name
        if not hasattr(content, 'mode'):
            content.mode = 'r'
        if not hasattr(content, 'size') and hasattr(content, 'len'):
            content.size = content.len
        if not content is File:
            content = File(content)
        name = self.storage and self.storage.save_file(name, content) or None
        if name:
            self.url = name
            self.identify(save=False)
            self.name = os.path.splitext(os.path.basename(name))[0]
            self.save(force_update_name=True)
        else:
            raise IOError("Media file could not be stored")

    def load_file(self):
        return self.storage and self.storage.load_file(self.url) or None

    def file_exists(self):
        return self.storage and self.storage.file_exists(self.url) or False

    @property
    def file_size(self):
        if self.file_exists():
            return self.storage.size(self.url)
        else:
            return None

    def delete_file(self):
        self.clear_derivatives()
        return self.storage and self.storage.storage_system.delete(self.url) or False

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
            width, height, bitrate = multimedia.identify(self.get_absolute_file_path())
            self.width = width
            self.height = height
            self.bitrate = bitrate
            if save:
                self.save()

    def clear_derivatives(self):
        for m in self.derivatives.all():
            m.delete_file()
        self.derivatives.all().delete()

    def is_local(self):
        return self.storage and self.storage.is_local()

    def is_downloadable_by(self, user):
        r, w, m, restrictions = get_effective_permissions_and_restrictions(user, self.storage)
        # if size or download restrictions exist, no direct download of a media file is allowed
        if restrictions and (restrictions.has_key('width') or
                             restrictions.has_key('height') or
                             restrictions.get('download', 'yes') == 'no'):
            return False
        else:
            return r

    def editable_by(self, user):
        return self.record.editable_by(user) and check_access(user, self.storage, write=True)

    def extract_text(self):
        if self.mimetype == 'text/plain':
            return self.load_file().read()
        elif self.mimetype == 'application/pdf':
            return extractTextFromPdfStream(self.load_file())
        else:
            return ''


class TrustedSubnet(models.Model):
    subnet = models.CharField(max_length=80)

    def __unicode__(self):
        return "TrustedSubnet (%s)" % self.subnet

class ProxyUrl(models.Model):
    uuid = models.CharField(max_length=36, unique=True)
    subnet = models.ForeignKey(TrustedSubnet)
    url = models.CharField(max_length=1024)
    context = models.CharField(max_length=256, null=True, blank=True)
    user = models.ForeignKey(User)
    user_backend = models.CharField(max_length=256, null=True, blank=True)
    last_access = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return 'ProxyUrl %s: %s (Ctx %s, Usr %s, Sbn %s)' % (self.uuid, self.url, self.context, self.user, self.subnet)

    def get_absolute_url(self):
        return reverse('storage-proxyurl', kwargs=dict(uuid=self.uuid))

    @staticmethod
    def create_proxy_url(url, context, ip, user):
        ip = IP(ip)
        for subnet in TrustedSubnet.objects.all():
            if ip in IP(subnet.subnet):
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
                                            defaults=dict(uuid=str(uuid.uuid4())))
        return proxy_url

    def get_additional_url(self, url):
        proxy_url, created = ProxyUrl.objects.get_or_create(
                                            subnet=self.subnet,
                                            url=url,
                                            context=self.context,
                                            user=self.user,
                                            user_backend=self.user_backend,
                                            defaults=dict(uuid=str(uuid.uuid4())))
        return proxy_url
