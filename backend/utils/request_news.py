import json
import os

import requests


def check_news(first=False) -> list:

    host = os.getenv("RSS_FEED_HOST") + ":1000"
    url = f"{host}/rss_feed/check_feed"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    data = json.dumps({'first': first})
    _ = requests.post(url, data=data, headers=headers)
    try:
        res = json.loads(_.content)['list']
    except Exception:
        raise
    return res