# -*- coding: utf-8 -*-

import requests
import json

HIPCHAT_MDID_URL = ('https://api.hipchat.com/v2/room/1178917/notification'
                    '?auth_token=1NZi9eeceS2ZUkKeJbIkotAq3OfHKVfOyPcC66UF')

payload = {
    'color': 'green',
    'message': ('The "MDID Workers" service had stopped!'
                ' The service has been restarted.'),
    'notify': False,
    'message_format': 'text',
}

headers = {'content-type': 'application/json'}

r = requests.post(HIPCHAT_MDID_URL, data=json.dumps(payload), headers=headers)
