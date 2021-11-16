import mimetypes
import os
import shutil
import sys
import traceback
from contextlib import contextmanager

from PIL import Image
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.conf import settings

from rooibos.data.models import Field, Collection
from rooibos.data.models import FieldValue
from rooibos.data.models import Record
from rooibos.solr.models import mark_for_update
from rooibos.storage.models import Storage


VALID_MIMETYPES = (
    'image/jpeg',
    'image/tiff',
)


class Command(BaseCommand):
    help = 'Import media files from directory'

    def add_arguments(self, parser):
        parser.add_argument('--storage', '-s', type=int, dest='storage',
                            required=True,
                            help='Storage identifier')
        parser.add_argument('--collection', '-c', type=int, dest='collection',
                            required=True,
                            help='Collection identifier')
        parser.add_argument('--identifier', '-i', dest='identifier_field',
                            default='dc.identifier',
                            help='Identifier field (default "dc.identifier")')
        parser.add_argument('--image-number', '-n', dest='image_number_field',
                            help='Optional image number field')
        parser.add_argument('--directory', '-d', dest='incoming_dir',
                            required=True,
                            help='Incoming directory')
        parser.add_argument('--archive', '-a', dest='archive_dir',
                            required=True,
                            help='Archive directory')
        parser.add_argument('--from', '-f', dest='from_email',
                            help='Sender email for report')
        parser.add_argument('--to', '-t', dest='to_email', action='append',
                            help='Recipient email for report')
        parser.add_argument('--jpeg', '-j', dest='convert_to_jpeg',
                            action='store_true',
                            help='Convert all images to JPEG')
        parser.add_argument('--quality', '-q', type=int, dest='quality',
                            default=70,
                            help='JPEG quality for converted '
                                 'images (default "70")')
        parser.add_argument('--max-size', '-m', type=int, dest='max_size',
                            default=4000,
                            help='Maximum side for converted '
                                 'images (default "4000")')

    def handle(self, storage, collection, incoming_dir, archive_dir,
               identifier_field=None, image_number_field=None,
               from_email=None, to_email=None, convert_to_jpeg=False,
               quality=70, max_size=4000, **kwargs):
        """
        Import and convert a set of JPEG or TIFF images into DIDO.
        """

        try:
            identifier_field = Field.get_by_name(identifier_field)
            if image_number_field:
                image_number_field = Field.get_by_name(image_number_field)

            if not os.path.exists(incoming_dir):
                print('Invalid incoming directory %s' % incoming_dir)
                sys.exit(1)

            if not os.path.exists(archive_dir):
                print('Invalid archive directory %s' % archive_dir)
                sys.exit(1)

            os.makedirs(settings.SCRATCH_DIR, exist_ok=True)

            if not os.listdir(incoming_dir):
                # No files to import - nothing to do!
                print('No files to import, exiting')
                sys.exit(0)

            # Set up the database access objects
            storage = Storage.objects.get(id=storage)
            Collection.objects.get(id=collection)

            collection_dir = storage.base

        except Exception:
            # Error accessing the database
            exception = traceback.format_exc()
            send_report(from_email, to_email, exception=exception)
            sys.exit(1)

        def generate_paths(fname, fid):
            """
            Generate and return a dict containing absolute paths to
            files relevant to the current image.
            """
            ext = '.jpg' if convert_to_jpeg else os.path.splitext(fname)[1]
            p = {
                'orig_file': os.path.join(incoming_dir, fname),
                'archive_dir': os.path.join(archive_dir, fid[:2]),
                'converted_file': os.path.join(collection_dir, fid + ext),
            }
            p['archive_file'] = os.path.join(p['archive_dir'], fname)
            return p

        # Set up metadata variables
        meta = {}
        exception = None

        try:
            with lock_file('mdid-import-media.lock'):
                for file_name in os.listdir(incoming_dir):
                    print("Attempting to import file %s..." % file_name)
                    file_id, _ = os.path.splitext(file_name)

                    file_type = mimetypes.guess_type(
                        os.path.join(incoming_dir, file_name),
                    )[0]
                    if file_type not in VALID_MIMETYPES:
                        print('Invalid filetype "%s", skipping %s' %
                              (file_type, file_name))
                        continue

                    # Generate absolute file paths for
                    # the original and new files
                    try:
                        print("Generating paths for %s..." % file_name)
                        paths = generate_paths(file_name, file_id)
                    except OSError:
                        exception = traceback.format_exc()
                        raise

                    if convert_to_jpeg and file_type != 'image/jpeg':
                        # Create the new images and save them, making sure not
                        # to re-compress if the image is already a jpeg
                        try:
                            print("Attempting to convert %s. File type: %s" % (
                                file_name, file_type))
                            convert_image(
                                paths['orig_file'],
                                paths['converted_file'],
                                quality,
                                max_size,
                            )
                        except IOError:
                            exception = traceback.format_exc()
                            raise
                    else:
                        shutil.copyfile(
                            paths['orig_file'], paths['converted_file'])

                    assert os.path.isfile(paths['converted_file']), \
                        '%s does not exist' % paths['converted_file']

                    # Create the database records for this file
                    try:
                        print("Attempting to see if this record "
                              "already exists in db...")
                        field_value = FieldValue.objects.get(
                            field=image_number_field,
                            value=file_id,
                            index_value=file_id[:32],
                        )
                    except FieldValue.DoesNotExist:
                        # Record doesn't exist, which means we need to create
                        # the initial record in the database.
                        print("No record found. Adding %s to database..." %
                              file_name)
                        duplicate = False
                        add_record_to_database(
                            file_id=file_id,
                            field=identifier_field,
                            storage=storage,
                            image_number=image_number_field,
                        )
                    else:
                        duplicate = True
                        record = field_value.record
                        print("Record already exists in database"
                              " - replacing file")
                        delete_thumbs(record=record)

                    # Move the original file to the archive directory
                    try:
                        os.makedirs(paths['archive_dir'], exist_ok=True)
                        print(
                            "Moving the original file %s to the archive..." %
                            file_name)
                        shutil.move(paths['orig_file'], paths['archive_file'])
                    except (IOError, OSError):
                        exception = traceback.format_exc()
                        raise

                    assert os.path.isfile(paths['archive_file']), \
                        '%s does not exist' % paths['archive_file']

                    # Add metadata to the meta dict
                    meta[file_id + '.jpg'] = {
                        'path': paths['converted_file'],
                        'duplicate': duplicate,
                    }

                    print()
                    print()
        except Exception:
            traceback.print_exc()
            raise
        finally:
            send_report(from_email, to_email, meta, exception)
            sys.exit(1 if exception else 0)


@contextmanager
def lock_file(lock):
    """
    Checks for the existence of a given lock file, and raises an exception
    if one exists. Removes the lock file when finished.

    Usage:
        with lock_file('path/to/file.lock'):
            # code to execute mutually exclusively
    """
    if os.path.exists(lock):
        raise EnvironmentError('Another import script is already running')
    else:
        open(lock, 'w')
        try:
            yield
        finally:
            os.remove(lock)


def convert_image(orig_file, new_file, quality=100, max_size=4000):
    """
    Converts an image file to JPEG and scales it based on the specified
    parameters.
    """
    with open(orig_file, 'r') as f:
        img = Image.open(f).convert('RGB')
        if max(img.size) > max_size:
            # Scales image so the longest side does not exceed 4000
            # pixels, preserving aspect ratio
            img.thumbnail(size=(max_size, max_size))
        img.save(new_file, format='JPEG', quality=quality)
        del img


def add_record_to_database(file_id, storage, field, image_number):
    """
    Add record and related metadata to the DB, and index the record in Solr.
    """
    new_filename = file_id + '.jpg'

    # Create the record object
    record = Record.objects.create()

    # Set values for relevant fields in the data_fieldvalue table
    record.fieldvalue_set.create(
        field=field,
        value=new_filename,
    )
    if image_number:
        record.fieldvalue_set.create(
            field=image_number,
            value=file_id,
        )

    # Create an entry in the storage_media table for this image
    record.media_set.create(
        storage=storage,
        url=new_filename,
        mimetype='image/jpeg',
    )

    # Store the record object in the database
    record.save()

    # Index the new record in solr
    mark_for_update(record.id)


def delete_thumbs(record):
    """
    Remove thumbnails for the given record so mdid3 will regenerate them.
    """
    for media in record.media_set.all():
        media.identify()
        path = media.storage.get_derivative_storage_path()
        for filename in os.listdir(path):
            if filename.startswith('%s-' % media.id):
                os.remove(os.path.join(path, filename))


def send_report(from_email, to_email, meta=None, exception=None):
    """
    Generate and email a report summarizing the files that were converted
    during the script's execution.
    """
    if not any([meta, exception]):
        # No report needs to be sent
        return

    report = 'This is an automatically generated message.\n\n'
    if exception:
        report += """
            An error occurred while attempting to run the
            import script.\n\n%s
        """ % exception
        subject = 'ERROR: Import report'
    else:
        report += 'The import.py script completed successfully.'
        subject = 'Import report'

    if meta:
        new_files = [
            '%s (stored at: %s)' % (k, v['path'])
            for k, v in meta.items()
            if not v['duplicate']
        ]
        duplicate_files = [
            '%s (stored at: %s)' % (k, v['path'])
            for k, v in meta.items()
            if v['duplicate']
        ]
        new_files.sort()
        duplicate_files.sort()
        if new_files:
            report += '\n\nNew imported files:\n' + '\n'.join(new_files)
        if duplicate_files:
            report += '\n\nReplaced files:\n' + '\n'.join(duplicate_files)

    if not from_email or not to_email:
        print(report)
        return

    send_mail(
        subject,
        report,
        from_email,
        to_email,
        fail_silently=False,
    )
