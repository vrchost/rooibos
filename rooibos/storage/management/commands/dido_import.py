#!/usr/bin/env python
# dido_import.py - DIDO image import and processing tool
# Author: James Gray <grayj@uvic.ca>
#
# This script will select all images in the 'incoming' directory,
# validate them, and create a set of jpeg derivatives, before archiving
# each original image in an archive directory.

import os
import shutil
import sys
import traceback

from rooibos.data.models import Field
from rooibos.data.models import FieldValue
from rooibos.data.models import Record
from rooibos.data.models import standardfield
from rooibos.settings_local import SCRATCH_DIR
from rooibos.storage.models import Storage

from config import ARCHIVE_DIR
from config import COLLECTION_DIR
from config import INCOMING_DIR
from config import MDID_COLLECTION_ID
from helpers import add_record_to_database
from helpers import convert_image
from helpers import delete_thumbs
from helpers import extract_mimetype
from helpers import generate_paths
from helpers import lock_file
from helpers import send_report

VALID_MIMETYPES = (
    'image/jpeg',
    'image/tiff',
)

def dido_import():
    """
    Import and convert a set of JPEG or TIFF images into DIDO.
    """
    thumb_dir = os.path.join(SCRATCH_DIR, MDID_COLLECTION_ID)

    assert all([
        os.path.exists(ARCHIVE_DIR),
        os.path.exists(COLLECTION_DIR),
        os.path.exists(INCOMING_DIR),
    ]), """Must specify location of directories in the INCOMING_DIR,
        ARCHIVE_DIR and COLLECTION_DIR config variables"""

    assert all([
        os.path.exists(SCRATCH_DIR),
        os.path.exists(thumb_dir),
    ]), """Must specify the location of the thumb directory in the SCRATCH_DIR
        mdid3 config variable, and the collection id in the MDID_COLLECTION_ID
        config variable"""

    if not os.listdir(INCOMING_DIR):
        # No files to import - nothing to do!
        print 'No files to import, exiting'
        sys.exit(0)

    try:
        # Set up the database access objects
        storage = Storage.objects.get(id=2)
        identifier_field = standardfield('identifier')
        image_number_field = Field.objects.get(label='Image Number')
    except Exception:
        # Error accessing the database
        exception = traceback.format_exc()
        send_report(exception=exception)
        sys.exit(1)

    try:
        # Set up metadata variables
        meta = {}
        exception = None
        with lock_file('dido.lock'):
            for file_name in os.listdir(INCOMING_DIR):
                print "Attempting to import file %s..." % file_name
                file_id, _ = os.path.splitext(file_name)

                file_type = extract_mimetype(
                    os.path.join(INCOMING_DIR, file_name),
                )
                if file_type not in VALID_MIMETYPES:
                    print 'Invalid filetype, skipping %s' % file_name
                    continue

                # Generate absolute file paths for the original and new files
                try:
                    print "Generating paths for %s..." % file_name
                    paths = generate_paths(file_name, file_id)
                except OSError:
                    exception = traceback.format_exc()
                    raise

                # Create the new images and save them, making sure not to
                # re-compress if the image is already a jpeg
                quality = 70 #if file_type == 'image/tiff' else 100
                try:
                    print "Attempting to convert %s. File type: %s" % (file_name, file_type)
                    convert_image(
                        paths['orig_file'],
                        paths['converted_file'],
                        quality,
                    )
                except IOError:
                    exception = traceback.format_exc()
                    raise

                # Move the original file to the archive directory
                try:
                    if not os.path.exists(paths['archive_dir']):
                        os.makedirs(paths['archive_dir'])
                    print "Moving the original file %s to the archive..." % file_name
                    shutil.move(paths['orig_file'], paths['archive_file'])
                except (IOError, OSError):
                    exception = traceback.format_exc()
                    raise

                assert os.path.isfile(paths['archive_file']), \
                    '%s does not exist' % paths['archive_file']
                assert os.path.isfile(paths['converted_file']), \
                    '%s does not exist' % paths['converted_file']

                # Create the database records for this file
                try:
                    print "Attempting to see if this record already exists in db..."
                    field_value = FieldValue.objects.get(
                        field=image_number_field,
                        value=file_id,
                        index_value=file_id[:32],
                    )
                except FieldValue.DoesNotExist:
                    # Record doesn't exist, which means we need to create
                    # the initial record in the database.
                    print "No record found. Adding %s to database..." % file_name
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
                    print "Record already exists in database - replacing file"
                    delete_thumbs(record=record, thumb_dir=thumb_dir)

                # Add metadata to the meta dict
                meta[file_id + '.jpg'] = {
                    'path': paths['converted_file'],
                    'duplicate': duplicate,
                }

                print
                print

    except EnvironmentError:
        exception = traceback.format_exc()
        raise
    except Exception as e:
        print e.message
        raise
    finally:
        send_report(meta, exception)
        sys.exit(1 if exception else 0)

if __name__ == '__main__':
    dido_import()
