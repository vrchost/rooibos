# -*- coding: utf-8 -*-

import requests
import json
import settings

payload = {
    'color': 'green',
    'message': ('The "MDID Workers" service had stopped!'
                ' The service has been restarted.'),
    'notify': False,
    'message_format': 'text',
}

headers = {'content-type': 'application/json'}

r = requests.post(settings.HIPCHAT_MDID_URL, data=json.dumps(payload),
        headers=headers)
