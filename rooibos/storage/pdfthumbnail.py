# This is a standalone script to create a thumbnail from a PDF.
# The gfx library crashes hard when processing some PDFs, so
# it needs to be run in a separate process to not take down the
# original process.

import sys


def _pdfthumbnail(infile, outfile):
    try:
        import gfx
    except ImportError:
        return None
    doc = gfx.open("pdf", infile)
    img = gfx.ImageList()
    img.setparameter("antialise", "1") # turn on antialising
    page1 = doc.getPage(1)
    img.startpage(page1.width, page1.height)
    page1.render(img)
    img.endpage()
    img.save(outfile)


if __name__ == '__main__':

    if len(sys.argv) < 3:
        sys.exit('Usage: %s pdffile outfile' % sys.argv[0])

    try:
        _pdfthumbnail(sys.argv[1], sys.argv[2])
        sys.exit(0)
    except Exception, ex:
        sys.exit(ex)
