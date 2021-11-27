import json
import os
import pathlib

import numpy as np
import pandas as pd
import torch

import backend.sentiment_models.transformer_model as tm
from backend.utils import params

MAX_LEN = params.token_max_len


def get_embedding(text, model, tokenizer):
    """Push input IDs through model. Stack and sum `layers` (last four by default).
    Select only those subword token outputs that belong to our word of interest
    and average them."""

    encoded = tokenizer.encode_plus(
        text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=MAX_LEN,
    )
    # Get all hidden states
    with torch.no_grad():
        output = model(**encoded, output_hidden_states=True)
    states = output.hidden_states
    # Stack and sum all requested layers
    # output = torch.stack([states[i] for i in layers]).sum(0).squeeze()
    output = states[-1].squeeze(0)
    return output.mean(dim=0).numpy().reshape(1, -1).tolist()[0]


def compute_similarity(a, b):
    result = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    return result


def sentiment_weighted_text_embedding(text, separator="|@|"):
    """Converts a piece of text with multiple paragraphs into single vector adjusting for sentiment"""

    parts = text.split(separator)
    list_of_vectors = []
    for par in parts:
        if par == "":
            continue
        a = get_embedding(par, tm.xlm_model, tm.tokenizer)
        sent = tm.predict_one(par)
        list_of_vectors.append((a, sent))

    first = np.array(list_of_vectors[0][0])
    for next in list_of_vectors[1:]:
        if next[1] == 0:
            first += np.array(next[0]) * (1 / len(list_of_vectors))
        else:
            first += np.array(next[0]) * (2 / len(list_of_vectors))

    return np.array(first)


def averaged_text_embedding(text, separator="|@|"):
    """Converts a piece of text with multiple paragraphs into single vector"""

    parts = text.split(separator)
    list_of_vectors = []
    for par in parts:
        if par == "":
            continue
        a = get_embedding(par, tm.xlm_model, tm.tokenizer)
        list_of_vectors.append(a)

    first = np.array(list_of_vectors[0])
    for next in list_of_vectors[1:]:
        first += np.array(next)
    first = first / len(list_of_vectors)
    return np.array(first)


if __name__ == "__main__":
    path = pathlib.Path(
        "/home/stbarkhatov/PycharmProjects/robo_news/luthon_news/tests/similarities"
    )
    files = os.listdir(path)
    texts = dict()

    jsons = []
    for trd_name in files:
        if ".json" not in trd_name:
            continue
        jsons.append(trd_name)

    dict_ = {
        "time": [],
        "ticker": [],
        "text": [],
        "target_time": [],
        "target_ticker": [],
        "target_text": [],
        "average": [],
        "weighted": [],
    }

    done_set = set()
    for i in jsons[:10]:
        for j in jsons[:10]:
            if (i, j) in done_set or (j, i) in done_set:
                continue
            if i == j:
                continue

            trd1 = open(path / i, "rb").read().decode("ISO-8859-1")
            _ = json.loads(trd1.replace("'", '"'))
            txt1 = _["TEXT"]
            dict_["ticker"].append(_["TICKER"])
            dict_["time"].append(_["NEWS_TIME"])
            dict_["text"].append(txt1)

            trd2 = open(path / j, "rb").read().decode("ISO-8859-1")
            _ = json.loads(trd2.replace("'", '"'))
            txt2 = _["TEXT"]
            dict_["target_ticker"].append(_["TICKER"])
            dict_["target_time"].append(_["NEWS_TIME"])
            dict_["target_text"].append(txt2)

            i_text = sentiment_weighted_text_embedding(txt1)
            j_text = sentiment_weighted_text_embedding(txt2)
            sim = compute_similarity(i_text, j_text)
            dict_["weighted"].append(sim)

            i_text = averaged_text_embedding(txt1)
            j_text = averaged_text_embedding(txt2)
            sim = compute_similarity(i_text, j_text)
            dict_["average"].append(sim)

            print(i, j)
            done_set.add((i, j))

    tab = pd.DataFrame(dict_)
    tab.to_excel("/home/stbarkhatov/result2.xlsx")
