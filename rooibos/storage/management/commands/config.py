# config_template.py - DIDO image import and processing tool configuration file
# Author: James Gray <grayj@uvic.ca>

INCOMING_DIR = '/home/mdid3/incoming/'
ARCHIVE_DIR = '/home/mdid3/archive/'
COLLECTION_DIR = '/home/mdid3/mdid-collections/FineArts/'
MDID_COLLECTION_ID = 'fine-arts-images'
SERVER = 'luke.finearts.uvic.ca'
FROM_ADDR = 'fineadmn@uvic.ca'
TO_ADDRS = (
    'finelogs@uvic.ca',
    'ihubner@uvic.ca'
)
