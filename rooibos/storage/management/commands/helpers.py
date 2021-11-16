# helpers.py - DIDO image import and processing tool helper functions
# Author: James Gray <grayj@uvic.ca>

import os
import smtplib
import subprocess

from PIL import Image
from contextlib import contextmanager
from email.mime.text import MIMEText
from rooibos.data.models import Record
from rooibos.solr.models import mark_for_update

from config import ARCHIVE_DIR
from config import COLLECTION_DIR
from config import FROM_ADDR
from config import INCOMING_DIR
from config import SERVER
from config import TO_ADDRS


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
        raise EnvironmentError('Another DIDO import script is already running')
    else:
        open(lock, 'w')
        try:
            yield
        finally:
            os.remove(lock)


def generate_paths(file_name, file_id):
    """
    Generate and return a dict containing absolute paths to files relevant
    to the current image.
    """
    paths = {
        'orig_file': os.path.join(INCOMING_DIR, file_name),
        'archive_dir': os.path.join(ARCHIVE_DIR, file_id[:2]),
        'converted_file': os.path.join(COLLECTION_DIR, file_id + '.jpg'),
    }
    paths['archive_file'] = os.path.join(paths['archive_dir'], file_name)

    return paths


def convert_image(orig_file, new_file, quality=100):
    """
    Converts an image file to JPEG and scales it based on the specified
    parameters.
    """
    with open(orig_file, 'r') as f:
        img = Image.open(f).convert('RGB')
        if max(img.size) > 4000:
            # Scales image so the longest side does not exceed 4000
            # pixels, preserving aspect ratio
            img.thumbnail(size=(4000, 4000))
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
    record.name = file_id
    record.save()

    # Index the new record in solr
    mark_for_update(record.id)


def delete_thumbs(record, thumb_dir):
    """
    Remove thumbnails for the given record so mdid3 will regenerate them.
    """
    for media in record.media_set.all():
        media.identify()
        path = media.storage.get_derivative_storage_path()
        for filename in os.listdir(path):
            if filename.startswith('%s-' % media.id):
                os.remove(os.path.join(path, filename))


def send_report(meta=None, exception=None):
    """
    Generate and email a report summarizing the files that were converted
    during the script's execution.
    """
    if not any([meta, exception]):
        # No report needs to be sent
        return

    report = 'This is an automatically generated message from %s.\n\n' % SERVER
    if exception:
        report += """
            An error occurred while attempting to run the DIDO
            import script.\n\n%s
        """ % exception
        subject = '[%s] ERROR: Import report' % SERVER
    else:
        report += 'The import.py script completed successfully.'
        subject = '[%s] Import report' % SERVER

    if meta:
        new_files = [
            '%s (stored at: %s)' % (k, v['path'])
            for k, v in meta.iteritems()
            if not v['duplicate']
        ]
        duplicate_files = [
            '%s (stored at: %s)' % (k, v['path'])
            for k, v in meta.iteritems()
            if v['duplicate']
        ]
        new_files.sort()
        duplicate_files.sort()
        if new_files:
            report += '\n\nNew imported files:\n' + '\n'.join(new_files)
        if duplicate_files:
            report += '\n\nReplaced files:\n' + '\n'.join(duplicate_files)

    report += '\n\nFine Arts Admin'
    msg = MIMEText(report)
    msg['Subject'] = subject
    msg['From'] = FROM_ADDR
    msg['To'] = ', '.join(TO_ADDRS)

    s = smtplib.SMTP('localhost')
    s.sendmail(FROM_ADDR, TO_ADDRS, msg.as_string())
    s.quit()


def extract_mimetype(filename):
    """
    Extracts the mimetype from a given file using the unix ``file`` command.
    """
    args = ['file', '-i', filename]
    p = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, _ = p.communicate()

    _, mimetype, _ = output.split(' ')  # Extract the mimetype
    mimetype = mimetype[:-1]  # Strip off trailing semicolon

    return mimetype
