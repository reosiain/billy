import json
import os

import numpy as np
import requests


def sentiment_weighted_text_embedding(text, separator="|@|"):

    host = os.getenv("SENT_APP_HOST") + ":1001"
    url = f"{host}/sentiment/weighted_embedding"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    data = json.dumps({'text': text})
    _ = requests.post(url, data=data, headers=headers)
    try:
        res = json.loads(_.content)['emb']
    except Exception:
        raise
    return np.array(res)


def averaged_text_embedding(text, separator="|@|"):

    host = os.getenv("SENT_APP_HOST") + ":1001"
    url = f"{host}/sentiment/average_embedding"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    data = json.dumps({'text': text})
    _ = requests.post(url, data = data, headers=headers)
    try:
        res = json.loads(_.content)['emb']
    except Exception:
        raise
    return np.array(res)


def compute_similarity(a, b):
    result = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    return result
