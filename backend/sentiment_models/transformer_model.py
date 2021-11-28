import json
import os

import requests


def predict(text: str) -> int:

    host = os.getenv("SENT_APP_HOST") + ":1001"
    url = f"http://{host}/sentiment/predict_many"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    data = json.dumps({'text': text})
    _ = requests.post(url, data = data, headers=headers)
    try:
        res = json.loads(_.content)['sentiment']
    except Exception:
        raise
    return int(res)


def predict_one(text: str) -> int:

    host = os.getenv("SENT_APP_HOST") + ":1001"
    url = f"http://{host}/sentiment/predict_one"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    data = json.dumps({'text': text})
    _ = requests.post(url, data = data, headers=headers)
    try:
        res = json.loads(_.content)['sentiment']
    except Exception:
        raise
    return int(res)
