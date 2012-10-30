from __future__ import with_statement
import Image
import StringIO
import logging
import mimetypes
import os
import re
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from rooibos.access import filter_by_access, get_effective_permissions_and_restrictions
from rooibos.data.models import Collection, Record, standardfield, standardfield_ids
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
    from rooibos.presentation.models import Presentation

    record_id = getattr(record, 'id', record)
    record = Record.filter_one_by_access(user, record_id)

    if not record:
        # Try to get to record through an accessible presentation -
        # own presentations don't count, since it's already established that owner
        # doesn't have access to the record.
        pw_q = Q(
            # Presentation must not have password
            Q(password=None) | Q(password='') |
            # or must know password
            Q(id__in=Presentation.check_passwords(passwords))
        )
        access_q = Q(
            # Must have access to presentation
            id__in=filter_by_access(user, Presentation),
            # and presentation must not be archived
            hidden=False
        )
        accessible_presentations = Presentation.objects.filter(
            pw_q, access_q, items__record__id=record_id)
        # Now get all the presentation owners so we can check if any of them have access
        # to the record
        owners = User.objects.filter(id__in=accessible_presentations.values('owner'))
        if not any(Record.filter_one_by_access(owner, record_id) for owner in owners):
            return Media.objects.none()

    return Media.objects.filter(
        record__id=record_id,
        storage__id__in=filter_by_access(user, Storage),
        )


try:
    import gfx
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def get_image_for_record(record, user=None, width=100000, height=100000, passwords={}, crop_to_square=False):
    media = get_media_for_record(record, user, passwords)
    q = Q(mimetype__startswith='image/')
    if settings.FFMPEG_EXECUTABLE:
        # also support video and audio
        q = q | Q(mimetype__startswith='video/') | Q(mimetype__startswith='audio/')
    if PDF_SUPPORT:
        q = q | Q(mimetype='application/pdf')

    media = media.select_related('storage').filter(q)

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
    if m.width > width or m.height > height or m.mimetype != 'image/jpeg' or not m.is_local():

        def derivative_image(master, width, height):
            if not master.file_exists():
                logging.error('Image derivative failed for media %d, cannot find file "%s"' % (master.id, master.get_absolute_file_path()))
                return None, (None, None)
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
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(output, 'JPEG', quality=85, optimize=True)
                return output.getvalue(), image.size
            except Exception, e:
                logging.error('Image derivative failed for media %d (%s)' % (master.id, e))
                return None, (None, None)

        # See if a derivative already exists
        name = '%s-%sx%s%s.jpg' % (m.id, width, height, 'sq' if crop_to_square else '')
        sp = m.storage.get_derivative_storage_path()
        if sp:
            if not os.path.exists(sp):
                try:
                    os.makedirs(sp)
                except:
                    # check if directory exists now, if so another process may have created it
                    if not os.path.exists(sp):
                        # still does not exist, raise error
                        raise
            path = os.path.join(sp, name)

            if not os.path.exists(path) or os.path.getsize(path) == 0:
                output, (w, h) = derivative_image(m, width, height)
                if output:
                    with file(path, 'wb') as f:
                        f.write(output)
                else:
                    return None
            return path

        else:
            return None

    else:

        return m.get_absolute_file_path()


def get_thumbnail_for_record(record, user=None, crop_to_square=False):
    return get_image_for_record(record, user, width=100, height=100, crop_to_square=crop_to_square)


def find_record_by_identifier(identifiers, collection, owner=None,
        ignore_suffix=False, suffix_regex=r'[-_]\d+$'):
    idfields = standardfield_ids('identifier', equiv=True)
    records = Record.by_fieldvalue(idfields, identifiers) \
                    .filter(collection=collection, owner=owner)
    if not records and ignore_suffix:
        if not isinstance(identifiers, (list, tuple)):
            identifiers = [identifiers]
        identifiers = (re.sub(suffix_regex, '', id) for id in identifiers)
        records = Record.by_fieldvalue(idfields, identifiers) \
                        .filter(collection=collection, owner=owner)
    return records


def match_up_media(storage, collection):
    broken, files = analyze_media(storage)
    # find records that have an ID matching one of the remaining files
    results = []
    for file in files:
        # Match identifiers that are either full file name (with extension) or just base name match
        filename = os.path.split(file)[1]
        id = os.path.splitext(filename)[0]
        records = find_record_by_identifier((id, filename,), collection, ignore_suffix=True)
        if len(records) == 1:
            results.append((records[0], file))
    return results


def analyze_records(collection, storage):
    # find empty records, i.e. records that don't have any media in the given storage
    return collection.records.exclude(id__in=collection.records.filter(media__storage=storage).values('id'))


def analyze_media(storage):
    broken = []
    extra = []
    # Storage must be able to provide file list
    if hasattr(storage, 'get_files'):
        # Find extra files, i.e. files in the storage area that don't have a matching media record
        files = storage.get_files()
        # convert to dict for faster lookup
        extra = dict(zip(files, [None] * len(files)))
        # Find broken media, i.e. media that does not have a related file on the file system
        for media in Media.objects.filter(storage=storage):
            url = os.path.normcase(os.path.normpath(media.url))
            if extra.has_key(url):
                # File is in use
                del extra[url]
            else:
                # missing file
                broken.append(media)
        extra = extra.keys()
    return broken, extra
