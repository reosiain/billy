import pickle

import pandas as pd

from backend.trade_actions import exit_model as em
from backend.utils import params

with open(
    "/home/stbarkhatov/Documents/News/News_sources/stocks_and_news/04052021/for_rl.pickle",
    "rb",
) as f:
    set_data = pickle.load(f)

smaller_set_data = {}

for i in range(len(set_data)):
    key = list(set_data.keys())[i]
    smaller_set_data[key] = set_data[key]

del set_data

cnt_good = 1
cnt_all = 1
cum_ret = 1

with open(params.source_root / f"backtesting/test.csv", "w") as f:
    f.close()

for e in smaller_set_data.keys():

    full_data = smaller_set_data[e]
    init_price = list(full_data[full_data["enter"] == 1]["CLOSE"])[0]
    init_index = full_data[full_data["enter"] == 1].index[0]
    last_index = full_data.index[-1]
    sentiment = full_data.sentiment.iloc[0]

    modulo = 1 if sentiment == 2 else -1

    prev_avg = 0
    probas = []
    for idx in range(init_index + 3, last_index):  # Now 10 minute force wait
        new_tab = pd.DataFrame(
            columns=[
                "ticker",
                "per",
                "date",
                "time",
                "OPEN",
                "HIGH",
                "LOW",
                "CLOSE",
                "VOL",
            ]
        )
        quotes = full_data.copy()
        quotes = quotes.loc[:idx]
        new_tab = new_tab.append(quotes)
        new_tab = new_tab[
            ["ticker", "per", "date", "time", "OPEN", "HIGH", "LOW", "CLOSE", "VOL"]
        ]
        features = em.produce_feature_series(ticker=None, quotes=new_tab)
        preds = []
        new_price = new_tab["CLOSE"].iloc[-1]
        retr = (new_price / init_price) - 1
        retr = retr * modulo

        if sentiment == 2:
            search = 2
        else:
            search = 0

        # if idx == init_index + 30:
        #    break
        # if retr <= -0.01:
        #    break
        line = features.iloc[-1]
        output = em.model.predict_proba(pd.DataFrame(line).T)[0]
        probas.append(output[search])

        avg = sum(probas[-2:]) / 5

        # Two conditions indication beginning of the cycle
        if prev_avg == 0:
            prev_avg = avg
            continue
        if len(probas) == 1:
            continue

        proba_change = (avg / prev_avg) - 1
        prev_avg = avg

        linr = (
            f"{idx};{output[0]};{output[2]};{retr};{sentiment};{new_price};{init_price}"
        )

        with open(params.source_root / f"backtesting/test.csv", "a") as f:
            f.write(linr)
            f.write("\n")

        # if proba_change <= -0.2 or avg <= 0.05:
        #    break
        # else:
        #    continue

    cnt_all += 1

    retr = (new_price / init_price) - 1
    retr = retr * modulo - 0.001
    if retr >= 0:
        cnt_good += 1

    time = idx - init_index
    too_long = False
    if idx == last_index or idx == last_index - 1:
        too_long = True

    cum_ret = cum_ret * (1 + (((new_price / init_price) - 1) * modulo))

    print("--------------------------------")
    print(f"Elapsed time: {time} minutes")
    print(f"Time break: {too_long}")
    print(f"Return: {round(retr * 100, 3)} %")
    print(f"Win rate so far: {round(cnt_good / (cnt_all + 1), 2) * 100} %")
    print(f"Cum ret: {round((cum_ret - 1) * 100, 2)}%")
    # print(f'Final probability: {round(avg*100, 2)}% on {sentiment}')
    print("--------------------------------")
    continue
