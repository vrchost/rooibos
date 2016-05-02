from __future__ import with_statement
from pyPdf.pdf import PdfFileReader


def extract_text_from_pdf_stream(stream):
    reader = PdfFileReader(stream)
    return '\n'.join(
        reader.getPage(i).extractText()
        for i in range(reader.getNumPages())
    )


def extract_text_from_pdf_file(filename):
    with open(filename, 'rb') as stream:
        return extract_text_from_pdf_stream(stream)
