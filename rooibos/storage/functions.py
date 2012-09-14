from __future__ import with_statement
from pyPdf.pdf import PdfFileReader


def extractTextFromPdfStream(stream):
    reader = PdfFileReader(stream)
    return '\n'.join(reader.getPage(i).extractText()
                    for i in range(reader.getNumPages()))

def extractTextFromPdfFile(filename):
    with open(filename, 'rb') as stream:
        return extractTextFromPdfStream(stream)
