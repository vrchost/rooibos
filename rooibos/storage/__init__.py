from __future__ import with_statement
import Image
import StringIO
import logging
import mimetypes
import os
from django.conf import settings
from django.db import connection
from django.db.models import Q, F
from rooibos.access import accessible_ids, get_effective_permissions_and_restrictions
from rooibos.data.models import Collection, Record, standardfield
from rooibos.presentation.models import Presentation
from models import Media, Storage


mimetypes.init([os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'mime.types'))])


# sort images by area
def _imgsizecmp(x, y):
    if x.width and x.height and y.width and y.height:
        return cmp(x.width * x.height, y.width * y.height)
    if x.width and x.height:
        return 1
    if y.width and y.height:
        return -1
    return 0


def get_media_for_record(record, user=None, passwords={}):
    """
    Returns all media accessible to the user either directly through collections
    or indirectly through presentations.
    A user always must have access to the storage where the media is stored.
    """

    if hasattr(record, 'id'):
        recordid = record.id
    else:
        recordid = record

    if user:
        ownercheck = Q(record__owner=user) if user.is_authenticated() and not user.is_superuser else Q()
    else:
        ownercheck = Q(record__owner=None)

    # get available media objects
    # Has access to collection containing record and to storage containing media
    media = Media.objects.filter(
        Q(record__collection__id__in=accessible_ids(user, Collection)) # record is accessible
        | ownercheck # or record is accessible via owner
        | Q(   # or presentation containing the record is accessible
            Q(record__presentationitem__presentation__password=None) |
            Q(record__presentationitem__presentation__in=Presentation.check_passwords(passwords)),
            record__presentationitem__presentation__id__in=accessible_ids(user, Presentation)
        ),
        storage__id__in=accessible_ids(user, Storage),  # storage always must be accessible
        record__id=recordid
    )

    return media


def get_image_for_record(record, user=None, width=100000, height=100000, passwords={}, crop_to_square=False, force_local=False):

    media = get_media_for_record(record, user, passwords)

    q = Q(mimetype__startswith='image/')
    if settings.FFMPEG_EXECUTABLE:
        # also support video and audio
         q = q | Q(mimetype__startswith='video/') | Q(mimetype__startswith='audio/')

    media = media.filter(q, master=None) # don't look for derivatives here

    if not media:
        return None

    map(lambda m: m.identify(lazy=True), media)

    media = sorted(media, _imgsizecmp, reverse=True)

    # find matching media
    last = None
    for m in media:
        if m.width > width or m.height > height:
            # Image still larger than given dimensions
            last = m
        elif (m.width == width and m.height <= height) or (m.width <= width and m.height == height):
            # exact match
            break
        else:
            # Now we have a smaller image
            m = last or m
            break

    # m is now equal or larger to requested size, or smaller but closest to the requested size

    # check what user size restrictions are
    restrictions = get_effective_permissions_and_restrictions(user, m.storage)[3]
    if restrictions:
        width = min(width, restrictions.get('width', width))
        height = min(height, restrictions.get('height', height))

    # see if image needs resizing
    if m.width > width or m.height > height or m.mimetype != 'image/jpeg' or (force_local and not m.is_local()):

        def derivative_image(master, width, height):
            import ImageFile
            ImageFile.MAXBLOCK = 16 * 1024 * 1024
            from multimedia import get_image
            try:
                file = get_image(master)
                image = Image.open(file)
                if crop_to_square:
                    w, h = image.size
                    if w > h:
                        image = image.crop(((w - h) / 2, 0, (w - h) / 2 + h, h))
                    elif w < h:
                        image = image.crop((0, (h - w) / 2, w, (h - w) / 2 + w))
                image.thumbnail((width, height), Image.ANTIALIAS)
                output = StringIO.StringIO()
                image.save(output, 'JPEG', quality=85, optimize=True)
                return output, image.size
            except Exception, e:
                logging.error('Could not create derivative image, exception: %s' % e)
                return None, (None, None)

        # See if a derivative already exists
        d = m.derivatives.filter(Q(width=width, height__lte=height) | Q(width__lte=width, height=height),
                                 # find a square derivative if requested, or if source is square,
                                 # otherwise look for a non-square (i.e. something matching the original aspect ratio)
                                 Q(width=F('height')) if crop_to_square or m.width == m.height else ~Q(width=F('height')),
                                 mimetype='image/jpeg')
        if d:
            # use derivative
            d = d[0]
            if not d.file_exists():
                # file has been removed, recreate
                output, (w, h) = derivative_image(m, width, height)
                if not output:
                    return None
                d.save_file('%s-%sx%s.jpg' % (d.id, w, h), output)
            m = d
        else:
            # create new derivative with correct size
            output, (w, h) = derivative_image(m, width, height)
            if not output:
                return None
            storage = m.storage.get_derivative_storage()
            m = Media.objects.create(record=m.record, storage=storage, mimetype='image/jpeg',
                                     width=w, height=h, master=m)
            m.save_file('%s-%sx%s.jpg' % (m.id, w, h), output)

    return m



def get_thumbnail_for_record(record, user=None, crop_to_square=False):
    return get_image_for_record(record, user, width=100, height=100, crop_to_square=crop_to_square)


def match_up_media(storage, collection):

    if not hasattr(storage, 'get_files'):
        return []

    # get list of files
    files = storage.get_files()

    # remove files that already have media objects
    for media in Media.objects.filter(storage=storage):
        try:
            files.remove(os.path.normpath(media.url))
        except ValueError:
            pass

    # find records that have an ID matching one of the remaining files
    idfields = standardfield('identifier', equiv=True)
    results = []
    for file in files:
        id = os.path.splitext(os.path.split(file)[1])[0]
        records = Record.by_fieldvalue(idfields, id).filter(collection=collection, owner=None)
        if len(records) == 1:
            results.append((records[0], file))

    return results
