# -*- coding: utf-8 -*-

import sys
import requests
import json
import xml.etree.ElementTree as ET
import settings # provides HIPCHAT_MDID_URL

# these will be the HipChat message colors based on the severity level
COLORS = {
    'Critical': 'red',
    'Error': 'red',
    'Warning': 'yellow',
    'Information': 'yellow',
    'Verbose': 'grey',
}

# helper to namespace the tags.  ElementTree isn't too smart about using
# xml namespaces...
def nstag(tag):
    return "{{{xmlns}}}{tag}".format(
            xmlns='http://schemas.microsoft.com/win/2004/08/events/event',
            tag=tag)

# grab the event xml from STDIN.  This is provided using the wevtutil.exe
# utility in a BAT file, and the output is piped in here
root = ET.fromstring(sys.stdin.read())

# fetch the EventRecordID out of <System> for reference
rec_id = root.find(nstag('System')).find(nstag('EventRecordID')).text

# fetch the Level and Message out of <RenderingInfo>
rendering_info = root.find(nstag('RenderingInfo'))
message = rendering_info.find(nstag('Message')).text
level = rendering_info.find(nstag('Level')).text

payload = {
    'color': COLORS[level],
    'message': '{message}\nEventRecordID: {rec_id}'.format(message=message,
        rec_id=rec_id),
    'notify': False,
    'message_format': 'text',
}

headers = {'content-type': 'application/json'}

r = requests.post(settings.HIPCHAT_MDID_URL, data=json.dumps(payload),
        headers=headers)

