import datetime
import time

import backend.utils.custom_now
import numpy as np
import pandas as pd
import ta
import tinvest
from backend import tinvest_api as api
from backend.tinvest_api.functions import get_candles_by_ticker
from backend.utils import params
from xgboost import XGBClassifier

models_source_path = params.exit_model_path
model = XGBClassifier()
model.load_model(models_source_path)


def produce_feature_series(ticker: str = None, **kwargs) -> pd.DataFrame:
    if "back_look" not in kwargs.keys():
        back_look = 3
    else:
        back_look = kwargs["back_look"]

    if "rolling_back_prediction" not in kwargs.keys():
        rolling_back_prediction = 5
    else:
        rolling_back_prediction = kwargs["rolling_back_prediction"]

    client = tinvest.SyncClient(api.TOKEN, use_sandbox=True)

    curr = backend.utils.custom_now.now()
    prev = curr - datetime.timedelta(minutes=60)

    raw_candles = get_candles_by_ticker(
        ticker, from_=prev, to=curr, interval="1min", client=client
    )
    candles = backend.tinvest_api.functions.unpack_candles(raw_candles)
    quotes = pd.DataFrame(
        candles, columns=["time", "OPEN", "CLOSE", "HIGH", "LOW", "VOL"]
    )

    rsi = ta.momentum.RSIIndicator(quotes["CLOSE"], window=20, fillna=True).rsi()
    ppo = ta.momentum.ppo_signal(
        quotes["CLOSE"], window_slow=60, window_fast=20, window_sign=10, fillna=True
    )
    roc = ta.momentum.roc(quotes["CLOSE"], window=20, fillna=True)

    # Volume
    force = ta.volume.force_index(
        quotes["CLOSE"], quotes["VOL"], window=60, fillna=True
    )
    vpt = ta.volume.VolumePriceTrendIndicator(
        quotes["CLOSE"], quotes["VOL"], fillna=True
    ).volume_price_trend()
    mfi = ta.volume.MFIIndicator(
        quotes["HIGH"],
        quotes["LOW"],
        quotes["CLOSE"],
        quotes["VOL"],
        window=60,
        fillna=True,
    ).money_flow_index()

    # Volatility
    bb_width = ta.volatility.BollingerBands(
        quotes["CLOSE"], window=20, window_dev=2, fillna=False
    ).bollinger_mavg()

    # Trend
    cci = ta.trend.CCIIndicator(
        quotes["HIGH"],
        quotes["LOW"],
        quotes["CLOSE"],
        window=20,
        constant=0.015,
        fillna=False,
    ).cci()
    adx = ta.trend.adx_neg(
        quotes["HIGH"], quotes["LOW"], quotes["CLOSE"], window=14, fillna=False
    )
    aroon_u = ta.trend.aroon_up(quotes["CLOSE"], window=25, fillna=False)
    aroon_d = ta.trend.aroon_down(quotes["CLOSE"], window=25, fillna=False)

    quotes.insert(len(quotes.columns), "mm_rsi", rsi)
    quotes.insert(len(quotes.columns), "mm_ppo", ppo)
    quotes.insert(len(quotes.columns), "mm_roc", roc)

    quotes.insert(len(quotes.columns), "vl_for", force)
    quotes.insert(len(quotes.columns), "vl_vpt", vpt)
    quotes.insert(len(quotes.columns), "vl_mfi", mfi)

    quotes.insert(len(quotes.columns), "vo_bbw", bb_width)

    quotes.insert(len(quotes.columns), "tr_cci", cci)
    quotes.insert(len(quotes.columns), "tr_adx", adx)
    quotes.insert(len(quotes.columns), "tr_aru", aroon_u)
    quotes.insert(len(quotes.columns), "tr_ard", aroon_d)
    quotes.replace([np.inf, -np.inf], 0, inplace=True)
    start = list(quotes.columns).index("mm_rsi")
    quotes = quotes[quotes.columns[start:]]

    changes = quotes.pct_change(back_look)
    quotes = quotes.join(changes, how="left", rsuffix="_change")
    features = quotes.iloc[-rolling_back_prediction:].copy()
    features.replace([np.inf, -np.inf], 0, inplace=True)

    return features


def predict_stock_direction(ticker: str, **kwargs) -> list:
    global model
    features = produce_feature_series(ticker)
    preds = []
    for row in range(len(features)):
        line = features.iloc[row]
        output = model.predict(pd.DataFrame(line).T)
        preds.append(output[0])

    return preds


def ready_to_close(ticker: str, sentiment: int) -> bool:
    sentiment = int(sentiment)
    prediction_series: list = predict_stock_direction(ticker)
    avg = sum(prediction_series) / len(prediction_series)

    if sentiment == 2:
        if avg <= 0.6:  # 2/5 indicate leave
            return True
        else:
            return False
    else:
        if avg >= 1.4:
            return True
        else:
            return False


if __name__ == "__main__":
    beg = time.time()
    print(ready_to_close("SBER", 0))
    print(f"{round(time.time() - beg, 2)} sec.")
