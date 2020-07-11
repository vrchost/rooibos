from django.conf import settings
import os
import tempfile
import wave
import struct
import re
import logging
import json as simplejson
import zipfile
from io import StringIO, BytesIO
from subprocess import Popen, PIPE
from rooibos.data.models import get_system_field
from PIL import Image


logger = logging.getLogger(__name__)


def _seconds_to_timestamp(seconds):
    hours = seconds // 3600
    minutes = seconds // 60
    seconds = seconds % 60
    return '%02d:%02d:%02d' % (hours, minutes, seconds)


def _run_ffmpeg(parameters, infile, outfile_ext):
    if not settings.FFMPEG_EXECUTABLE:
        return None
    handle, filename = tempfile.mkstemp(outfile_ext)
    os.close(handle)
    try:
        cmd = 'ffmpeg -i "%s" %s -y "%s"' % (infile, parameters, filename)
        logging.debug('_run_ffmpeg: %s' % cmd)
        cmd = [p.strip('"') for p in cmd.split()]
        ffmpeg = Popen(
            cmd,
            executable=settings.FFMPEG_EXECUTABLE,
            stdout=PIPE,
            stderr=PIPE
        )
        (output, errors) = ffmpeg.communicate()
        file = open(filename, 'rb')
        result = BytesIO(file.read())
        file.close()
        return result, output, errors
    except Exception as ex:
        logging.error("%s: %s" % (cmd, ex))
        return None, None, None
    finally:
        os.remove(filename)


def _which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def _pdfthumbnail(infile):
    logger.debug('Creating PDF thumbnail for %s' % infile)
    handle, filename = tempfile.mkstemp('.jpg')
    os.close(handle)
    try:
        executable = _which('pdftoppm') or 'pdftoppm'
        cmd = [
            executable,
            '-singlefile',
            '-scale-to', '800',
            '-jpeg',
            '-aa', 'yes',
            '-aaVector', 'yes',
            infile,
            os.path.splitext(filename)[0],
        ]
        logger.debug('Running %s' % cmd)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        (output, errors) = proc.communicate()
        logger.debug('output "%s" errors "%s"' % (output, errors))
        file = open(filename, 'rb')
        result = BytesIO(file.read())
        file.close()
        return result, output, errors
    except:
        logger.exception('Could not create PDF thumbnail')
        return None, None, None
    finally:
        os.remove(filename)


def identify(file):
    try:
        cmd = 'ffmpeg -i "%s"' % (file)
        ffmpeg = Popen(
            cmd,
            executable=settings.FFMPEG_EXECUTABLE,
            stdout=PIPE,
            stderr=PIPE
        )
        (output, errors) = ffmpeg.communicate()
        match = re.search(r'bitrate: (\d+) kb/s', errors)
        bitrate = int(match.group(1)) if match else None
        match = re.search(r'Video: .+ (\d+)x(\d+)', errors)
        width = int(match.group(1)) if match else None
        height = int(match.group(2)) if match else None
        logging.debug('Identified %s: %dx%d %d' % (
            file, width or 0, height or 0, bitrate or 0))
        return width, height, bitrate
    except Exception as e:
        logging.debug('Error identifying %s: %s' % (file, e))
        return None, None, None


def capture_video_frame(videofile, offset=5):
    logging.debug('capture_video_frame: %s (offset %s)' % (videofile, offset))
    params = '-r 1 -ss %s -t 00:00:01 -vframes 1 -f image2' % \
        _seconds_to_timestamp(offset)
    frame, output, errors = _run_ffmpeg(params, videofile, '.jpg')
    return frame


def render_audio_waveform(audiofile, basecolor, background, left, top,
                          height, width, max_only):
    wave_file, output, errors = _run_ffmpeg(
        '-t 00:00:30 -ar 8192 -ac 1', audiofile, '.wav')
    if not wave_file:
        return None
    file = wave.open(wave_file, 'rb')
    data = file.readframes(30 * 8192)
    frames = struct.unpack('%sh' % (len(data) // 2), data)
    image = Image.open(background)
    pix = image.load()
    lf = len(frames)
    if not max_only:
        height = height // 2
    middle = top + height
    basecolor = tuple(basecolor)
    lows, highs = [], []
    for x in range(width):
        f, t = (x * lf) // width, ((x + 1) * lf) // width
        lows.append(min(frames[f:t]))
        highs.append(max(frames[f:t]))
    low, high = abs(min(lows)), abs(max(highs))
    lows = [v * height // low for v in lows]
    highs = [v * height // high for v in highs]
    for x in range(width):
        high = middle - highs[x]
        low = middle - lows[x]
        for y in range(high, middle):
            pix[left + x, y] = basecolor
        if not max_only:
            for y in range(middle, low):
                pix[left + x, y] = basecolor
    output = BytesIO()
    image.save(output, 'JPEG', quality=85, optimize=True)
    output.seek(0)
    return output


def render_audio_waveform_by_mimetype(audiofile, mimetype):
    path = getattr(
        settings,
        'AUDIO_THUMBNAILS',
        os.path.join(settings.STATIC_DIR, 'images', 'audiothumbs')
    )
    mimetype = mimetype.split('/')[1]
    formatfile = os.path.join(path, mimetype + '.json')
    if not os.path.isfile(formatfile):
        formatfile = os.path.join(path, 'generic.json')
    format = simplejson.load(open(formatfile, 'r'))
    return render_audio_waveform(
        audiofile,
        format['color'],
        os.path.join(path, format['background']),
        format['left'],
        format['top'],
        format['height'],
        format['width'],
        format['max_only']
    )


def render_pdf(pdffile):
    image, output, errors = _pdfthumbnail(pdffile)
    return image


def thumbnail_from_pptx(pptxfile):
    try:
        with zipfile.ZipFile(pptxfile, 'r') as pptx:
            image = BytesIO(pptx.open('docProps/thumbnail.jpeg').read())
            image.seek(0)
            return image
    except:
        logging.debug(
            'Cannot extract thumbnail from PPTX file %s' % pptxfile,
            exc_info=True,
        )


def get_image(media):
    logging.debug('get_image: %s (%s)' % (
        media.get_absolute_file_path(), media.mimetype))
    image = None
    if media.mimetype.startswith('image/'):
        image = media.load_file()
    elif media.mimetype.startswith('video/'):
        # retrieve offset if available
        try:
            offset = int(media.record.fieldvalue_set.filter(
                field=get_system_field(),
                label='thumbnail-offset',
            )[0].value)
        except (IndexError, ValueError):
            offset = 5
        image = capture_video_frame(
            media.get_absolute_file_path(), offset=offset)
    elif media.mimetype.startswith('audio/'):
        image = render_audio_waveform_by_mimetype(
            media.get_absolute_file_path(), media.mimetype)
    elif media.mimetype == 'application/pdf':
        image = render_pdf(media.get_absolute_file_path())
    elif media.url.endswith('.pptx'):
        image = thumbnail_from_pptx(media.get_absolute_file_path())
    return image


def overlay_image_with_mimetype_icon(image, mimetype):
    """
    Overlays an image with an icon in the lower right corner
    No scaling of image or overlay icon
    Image must be a file-like object
    @returns a file-like object with the new image, or the same object if no
    overlay was found
    """
    path = os.path.join(
        os.path.dirname(__file__), '..', 'static', 'images', 'overlays')
    overlay = os.path.join(path, mimetype.replace('/', '_') + ".png")
    if not os.path.exists(overlay):
        overlay = os.path.join(path, mimetype.split('/')[0] + ".png")
    if not os.path.exists(overlay):
        return image

    if not isinstance(image, Image.Image):
        original_image = Image.open(image)
    else:
        original_image = image

    overlay_image = Image.open(open(overlay, 'rb'))
    pos = (original_image.size[0] - overlay_image.size[0],
           original_image.size[1] - overlay_image.size[1])
    original_image.paste(overlay_image, pos, overlay_image)

    if isinstance(image, Image.Image):
        return image

    output = BytesIO()
    original_image.save(output, 'JPEG', quality=85, optimize=True)
    output.seek(0)
    return output
