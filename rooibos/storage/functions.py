from __future__ import with_statement
from pyPdf.pdf import PdfFileReader
from PIL import Image
from StringIO import StringIO


def extract_text_from_pdf_stream(stream):
    reader = PdfFileReader(stream)
    return '\n'.join(
        reader.getPage(i).extractText()
        for i in range(reader.getNumPages())
    )


def extract_text_from_pdf_file(filename):
    with open(filename, 'rb') as stream:
        return extract_text_from_pdf_stream(stream)


EXIF_ORIENTATION = 274

# http://www.galloway.me.uk/2012/01/uiimageorientation-exif-orientation-sample-images/
# https://gist.github.com/steipete/4666527

# case 1: o = UIImageOrientationUp; break;
# case 3: o = UIImageOrientationDown; break;
# case 8: o = UIImageOrientationLeft; break;
# case 6: o = UIImageOrientationRight; break;
# case 2: o = UIImageOrientationUpMirrored; break;
# case 4: o = UIImageOrientationDownMirrored; break;
# case 5: o = UIImageOrientationLeftMirrored; break;
# case 7: o = UIImageOrientationRightMirrored; break;

EXIF_MIRRORED = [
    None,  # orientation starts at index 1
    False,
    True,
    False,
    True,
    True,
    False,
    True,
    False,
]

EXIF_ROTATION = [
    0,  # orientation starts at index 1
    0,
    0,
    180,
    180,
    270,
    270,
    90,
    90,
]


def rotateImageBasedOnExif(stream):
    image = Image.open(stream)

    try:
        orientation = image._getexif().get(EXIF_ORIENTATION, 1)
    except (IndexError, KeyError, AttributeError):
        orientation = 1

    mirror = EXIF_MIRRORED[orientation]
    rotate = EXIF_ROTATION[orientation]

    if not mirror and not rotate:
        return stream

    if rotate:
        image = image.transpose(getattr(Image, 'ROTATE_%d' % rotate))
    if mirror:
        image = image.transpose(Image.FLIP_LEFT_RIGHT)

    buffer = StringIO()
    image.save(buffer, 'jpeg', quality=85)

    return buffer
