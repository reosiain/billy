import datetime
import json
import time
from pathlib import Path

import pandas as pd

import backend.trade_actions.trade_entity_class as tr_cl
from backend.open_trade import check_closing_decision
from backend.trade_actions.active_trades_cache import Cache

quotes_path = Path(__file__).parent / "bad_day_trades/" / "CHMF.csv"
trade_path = (
    Path(__file__).parent / "bad_day_trades/trades" / "CHMF_21092021_102748_0.json"
)

with open(trade_path, "rb") as f:
    trade = json.load(f)

quotes = pd.read_csv(quotes_path)
time_delta = 200
init_cache = Cache.read()


def mock_msg():
    print("Message sent")


def mocked_now():
    global trade
    global time_delta
    dt = datetime.datetime.fromisoformat(trade["NEWS_TIME"]) + datetime.timedelta(
        seconds=time_delta
    )
    time_delta += 10
    return dt


def test_trade_closure(mocker):
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())
    mocker.patch(
        "backend.telegram_bot.bot_poster.select_message_and_post", return_value=mock_msg
    )

    global trade
    news_time = datetime.datetime.fromisoformat(trade["NEWS_TIME"])
    seq = trade["TEXT"]
    ticker = trade["TICKER"]

    constructed = tr_cl.Trade(time=news_time, seq=seq, ticker=ticker)

    Cache.overwrite([])
    Cache.append(constructed)

    for i in range(20):
        try:
            check_closing_decision()
        except:
            break
        print(mocked_now())
        time.sleep(1)

    print(mocked_now())
    global init_cache
    Cache.overwrite(init_cache)
