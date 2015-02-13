# -*- coding: utf-8 -*-

import requests
import json
import settings

payload = {
    'color': 'red',
    'message': ('The "MDID Workers" service had stopped!'
                ' Not restarting the service this time, it has been'
                ' stopped/restarted twice already.'),
    'notify': False,
    'message_format': 'text',
}

headers = {'content-type': 'application/json'}

r = requests.post(settings.HIPCHAT_MDID_URL, data=json.dumps(payload),
        headers=headers)
