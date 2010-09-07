from django.conf import settings
import os
import tempfile
import wave
import struct
import re
import logging
from django.utils import simplejson
from StringIO import StringIO
from subprocess import Popen, PIPE
import Image

def _seconds_to_timestamp(seconds):
    hours = seconds / 3600
    minutes = seconds / 60
    seconds = seconds % 60
    return '%02d:%02d:%02d' % (hours, minutes, seconds)

def _run_ffmpeg(parameters, infile, outfile_ext):
    if not settings.FFMPEG_EXECUTABLE:
        return None
    handle, filename = tempfile.mkstemp(outfile_ext)
    os.close(handle)
    try:
        cmd = 'ffmpeg -i "%s" %s -y "%s"' % (infile, parameters, filename)
        ffmpeg = Popen(cmd, executable=settings.FFMPEG_EXECUTABLE, stdout=PIPE, stderr=PIPE)
        (output, errors) = ffmpeg.communicate()
        file = open(filename, 'rb')
        result = StringIO(file.read())
        file.close()
        return result, output, errors
    except:
        return None, None, None
    finally:
        os.remove(filename)


def identify(file):
    try:
        cmd = 'ffmpeg -i "%s"' % (file)
        ffmpeg = Popen(cmd, executable=settings.FFMPEG_EXECUTABLE, stdout=PIPE, stderr=PIPE)
        (output, errors) = ffmpeg.communicate()
        match = re.search(r'bitrate: (\d+) kb/s', errors)
        bitrate = int(match.group(1)) if match else None
        match = re.search(r'Video: .+ (\d+)x(\d+)', errors)
        width = int(match.group(1)) if match else None
        height = int(match.group(2)) if match else None
        logging.debug('Identified %s: %dx%d %d' % (file, width or 0, height or 0, bitrate or 0))
        return width, height, bitrate
    except Exception, e:
        logging.debug('Error identifying %s: %s' % (file, e))
        return None, None, None
    

def capture_video_frame(videofile, offset=5):
    params = '-r 1 -ss %s -t 00:00:01 -vframes 1 -f image2' % _seconds_to_timestamp(offset)
    frame, output, errors = _run_ffmpeg(params, videofile, '.jpg')
    return frame

def render_audio_waveform(audiofile, basecolor, background, left, top, height, width, max_only):
    wave_file, output, errors = _run_ffmpeg('-t 00:00:30 -ar 8192 -ac 1', audiofile, '.wav')
    if not wave_file:
        return None
    file = wave.open(wave_file, 'rb')
    data = file.readframes(30 * 8192)
    frames = struct.unpack('%sh' % (len(data) / 2), data)
    image = Image.open(background)
    pix = image.load()
    lf = len(frames)
    if not max_only:
        height = height / 2
    middle = top + height
    basecolor = tuple(basecolor)
    lows, highs = [], []
    for x in range(width):
        f, t = (x * lf) / width, ((x + 1) * lf) / width
        lows.append(min(frames[f:t]))
        highs.append(max(frames[f:t]))
    low, high = abs(min(lows)), abs(max(highs))
    lows = map(lambda v: v * height / low, lows)
    highs = map(lambda v: v * height / high, highs)
    for x in range(width):
        high = middle - highs[x]
        low = middle - lows[x]
        for y in range(high, middle):
            pix[left + x, y] = basecolor
        if not max_only:
            for y in range(middle, low):
                pix[left + x, y] = basecolor
    output = StringIO()
    image.save(output, 'JPEG', quality=85, optimize=True)
    output.seek(0)
    return output

def render_audio_waveform_by_mimetype(audiofile, mimetype):
    path = getattr(settings, 'AUDIO_THUMBNAILS', os.path.join(settings.STATIC_DIR, 'images', 'audiothumbs'))
    mimetype = mimetype.split('/')[1]
    formatfile = os.path.join(path, mimetype + '.json')
    if not os.path.isfile(formatfile):
        formatfile = os.path.join(path, 'generic.json')
    format = simplejson.load(open(formatfile, 'r'))
    return render_audio_waveform(audiofile, format['color'], os.path.join(path, format['background']),
                                 format['left'], format['top'], format['height'], format['width'],
                                 format['max_only'])

def get_image(media):
    if media.mimetype.startswith('image/'):
        return media.load_file()
    if media.mimetype.startswith('video/'):
        return capture_video_frame(media.get_absolute_file_path())
    if media.mimetype.startswith('audio/'):
        return render_audio_waveform_by_mimetype(media.get_absolute_file_path(), media.mimetype)
    return None
