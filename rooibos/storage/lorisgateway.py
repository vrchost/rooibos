import os
from io import StringIO
from loris.webapp import Loris, read_config
from loris.resolver import SimpleFSResolver
from werkzeug.wrappers import Request
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404


class CustomResolver(SimpleFSResolver):

    def __init__(self, ident, config):
        super(CustomResolver, self).__init__(config)
        self.ident = ident

    def resolve(self, app, ident, base_uri):
        info = super(CustomResolver, self).resolve(app, ident, base_uri)
        info.ident = self.ident
        return info


class CustomLoris(Loris):

    def __init__(self, resolver, app_configs):
        self.custom_resolver = resolver
        super(CustomLoris, self).__init__(app_configs)

    def _load_resolver(self):
        return self.custom_resolver


def handle_loris_request(request, filepath, record_id, record_name):

    config = read_config(StringIO(LORIS_CONF))

    config['logging']['log_level'] = 'DEBUG'

    config['logging']['log_dir'] = os.path.join(
        settings.SCRATCH_DIR, 'loris_log')
    if not os.path.exists(config['logging']['log_dir']):
        os.makedirs(config['logging']['log_dir'])
    config['loris.Loris']['tmp_dp'] = os.path.join(
        settings.SCRATCH_DIR, 'loris_tmp')
    if not os.path.exists(config['loris.Loris']['tmp_dp']):
        os.makedirs(config['loris.Loris']['tmp_dp'])
    config['loris.Loris']['enable_caching'] = False

    config['resolver']['src_img_root'] = os.path.dirname(filepath)

    basename = os.path.basename(filepath)

    ident = '//' + request.META.get(
        'HTTP_X_FORWARDED_HOST', request.META['HTTP_HOST'])
    ident += reverse(
        'storage-retrieve-iiif-image', args=(record_id, record_name))
    ident = ident.rstrip('/')

    resolver = CustomResolver(ident, config['resolver'])

    loris = CustomLoris(resolver=resolver, app_configs=config)
    environ = request.environ
    # remove prefixes
    environ['PATH_INFO'] = ('/%s/' % basename) + \
        '/'.join(environ['PATH_INFO'].split('/')[5:])
    werkzeug_request = Request(environ)

    response = loris.route(werkzeug_request)

    if response.status_code != 200:
        raise Http404()

    http_response = HttpResponse(
        content=response.get_data(),
        content_type=response.headers['Content-Type'],
    )
    http_response['Access-Control-Allow-Origin'] = '*'
    return http_response


LORIS_CONF = """
# loris2.conf
#
# This file is parsed by the ConfigObj library:
#
# <http://www.voidspace.org.uk/python/configobj.html>
#
# ConfigObj uses an ini-like syntax with a few important changes and extensions,
# which are explained here:
#
# <http://www.voidspace.org.uk/python/configobj.html#config-files>
#
# Note that 'unrepr' mode is used, which means that values are parsed as Python
# datatypes, e.g. strings are in quotes, integers are not, True is used for the
# boolean value TRUE, False for the boolean value FALSE, and lists are in []
# with commas (',') as the separators.
#
# <http://www.voidspace.org.uk/python/configobj.html#unrepr-mode>
#
# String interpolation is enabled using the "template" style. OS environment
# variables are available for interpolation, e.g., run_as_user='$USER'
#
# <http://www.voidspace.org.uk/python/configobj.html#string-interpolation>
#

[loris.Loris]
tmp_dp = '/tmp/loris2/tmp' # r--
www_dp = '/var/www/loris2' # r-x
run_as_user = 'loris'
run_as_group = 'loris'
enable_caching = True
redirect_canonical_image_request = False
redirect_id_slash_to_info = True

# max_size_above_full restricts interpolation of images on the server.
# Default value 200 means that a user cannot request image sizes greater than
# 200% of original image size (width or height).
# Set this value to 100 to disallow interpolation. Set to 0 to remove
# size restriction.
max_size_above_full = 200

#proxy_path=''
# cors_regex = ''
# NOTE: If supplied, cors_regex is passed to re.search():
#    https://docs.python.org/2/library/re.html#re.search
# Any url_root:
#    http://werkzeug.pocoo.org/docs/latest/wrappers/#werkzeug.wrappers.BaseRequest.url_root
# (i.e., https?://domain.edu(:port)?/) that matches will be
# set to the value of Access-Control-Allow-Origin.

[logging]
log_to = 'file'    # 'console'|'file'
log_level = 'INFO' # 'DEBUG'|'INFO'|'WARNING'|'ERROR'|'CRITICAL'
log_dir = '/var/log/loris2' # rw-
max_size = 5242880 # 5 MB
max_backups = 5
format = '%(asctime)s (%(name)s) [%(levelname)s]: %(message)s'

[resolver]
impl = 'loris.resolver.SimpleFSResolver'
src_img_root = '/usr/local/share/images' # r--

#Example of one version of SimpleHTTResolver config

#[resolver]
#impl = 'loris.resolver.SimpleHTTPResolver'
#source_prefix='https://<server>/fedora/objects/'
#source_suffix='/datastreams/accessMaster/content'
#cache_root='/usr/local/share/images/loris'
#user='<if needed else remove this line>'
#pw='<if needed else remove this line>'
#cert='<SSL client cert for authentication>'
#key='<SSL client key for authentication>'
#ssl_check='<Check for SSL errors. Defaults to True. Set to False to ignore issues with self signed certificates>'

# Sample config for TemplateHTTResolver config
# [resolver]
# impl = 'loris.resolver.TemplateHTTPResolver'
# cache_root='/usr/local/share/images/loris'
## optional settings
# delimiter = "|" # optional delimiter for splitting identifier, allowing for n-values to be inserted into the template
# default_format
# head_resolvable = False
# templates = 'a, b, fedora, devfedora, fedora_obj_ds'
# [[a]]
# url='http://example.edu/images/%s'
# [[b]]
# url='http://example.edu/images-elsewhere/%s'
## optional overrides for requests using this template
# user='otheruser'
# pw='secret'
# [[fedora]]
# url='http://<server>/fedora/objects/%s/datastreams/accessMaster/content'
## optional overrides for requests using this template
# cert='/path/to/client.pem'
# key='/path/to/client.key'
# [[fedora_obj_ds]]
# url = 'http://<server>/fedora/objects/%s/datastreams/%s/content' # as used with delimiter option below

[img.ImageCache]
cache_dp = '/var/cache/loris' # rwx

[img_info.InfoCache]
cache_dp = '/var/cache/loris' # rwx

[transforms]
dither_bitonal_images = False
target_formats = ['jpg','png','gif','webp']

    [[jpg]]
    impl = 'JPG_Transformer'

    [[tif]]
    impl = 'TIF_Transformer'

    [[png]]
    impl = 'PNG_Transformer'

    [[jp2]]
    impl = 'KakaduJP2Transformer'
    tmp_dp = '/tmp/loris/tmp/jp2' # rwx
    kdu_expand = '/usr/local/bin/kdu_expand' # r-x
    kdu_libs = '/usr/local/lib' # r--
    num_threads = '4' # string!
    mkfifo = '/usr/bin/mkfifo' # r-x
    map_profile_to_srgb = False
    srgb_profile_fp = '/usr/share/color/icc/colord/sRGB.icc' # r--

#   Sample config for the OpenJPEG Transformer

#   [[jp2]]
#   src_format = 'jp2'
#   impl = 'OPJ_JP2Transformer'
#   tmp_dp = '/tmp/loris/tmp/jp2' # rwx
#   opj_decompress = '/usr/local/bin/opj_decompress' # r-x
#   opj_libs = '/usr/local/lib' # r--
#   mkfifo = '/usr/bin/mkfifo' # r-x
#   map_profile_to_srgb = True
#   srgb_profile_fp = '/usr/share/color/icc/colord/sRGB.icc' # r--
"""
