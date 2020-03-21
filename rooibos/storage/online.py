import urllib.request, urllib.error, urllib.parse
import io


class OnlineStorageSystem():

    def __init__(self, base=None, storage=None):
        pass

    def get_absolute_media_url(self, media):
        return media.url

    def get_absolute_file_path(self, media):
        return None

    def open(self, url):
        # TODO: this can be a security issue if file:/// urls are allowed
        return io.BytesIO(urllib.request.urlopen(url).read())

    def exists(self, url):
        # TODO
        return True

    def size(self, url):
        return None

    def is_local(self):
        return False

    def load_file(self, media):
        return self.open(media.url)
