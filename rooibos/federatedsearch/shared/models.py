from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from rooibos.access import filter_by_access, check_access
from rooibos.access.models import AccessControl
from rooibos.util import unique_slug
from rooibos.util.caching import get_cached_value, cache_get, cache_get_many, cache_set, cache_set_many
import logging
import random
import types
from os import urandom
from base64 import b64encode, b64decode
from Crypto.Cipher import ARC4


def get_value(name):
    def f(self):
        v = getattr(self, 'e_%s'%name)
        return SharedCollection.decrypt(v) if v else v
    return f


def set_value(name):
    def f(self, value):
        setattr(self, 'e_%s'%name, SharedCollection.encrypt(value))
    return f


class SharedCollection(models.Model):
    SALT_SIZE = 8

    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True, blank=True)
    e_url = models.TextField(blank=True)
    e_username = models.TextField(blank=True)
    e_password = models.TextField(blank=True)
    description = models.TextField(blank=True)

    @staticmethod
    def encrypt(plaintext):
        salt = urandom(SharedCollection.SALT_SIZE)
        arc4 = ARC4.new(salt + settings.SECRET_KEY)
        plaintext = plaintext.encode('utf8')
        plaintext = "%3d%s" % (len(plaintext), plaintext) + urandom(256-len(plaintext))
        return "%s$%s" % (b64encode(salt), b64encode(arc4.encrypt(plaintext)))

    @staticmethod
    def decrypt(ciphertext):
        salt, ciphertext = map(b64decode, ciphertext.split('$'))
        arc4 = ARC4.new(salt + settings.SECRET_KEY)
        plaintext = arc4.decrypt(ciphertext)
        plaintext = plaintext[3:3+int(plaintext[:3].strip())]
        return plaintext.decode('utf8')

    def encrypted_property(name):
        return property(get_value(name), set_value(name))

    class Meta:
        ordering = ['title']

    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name',
                    check_current_slug=kwargs.get('force_insert'))
        super(SharedCollection, self).save(kwargs)

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.name)

    url = encrypted_property('url')
    username = encrypted_property('username')
    password = encrypted_property('password')
