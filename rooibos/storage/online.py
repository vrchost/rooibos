from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
import os
import random
import urllib2
import StringIO

class OnlineStorageSystem():

    def __init__(self, base=None):
        pass

    def get_absolute_media_url(self, storage, media):
        return media.url

    def get_absolute_file_path(self, storage, media):
        return None

    def open(self, url):
        # TODO: this can be a security issue if file:/// urls are allowed
        return StringIO.StringIO(urllib2.urlopen(url).read())

    def exists(self, url):
        # TODO
        return True

    def size(self, url):
        return None

    def is_local(self):
        return False
