import datetime

import tinvest

import backend.tinvest_api.functions as api
import backend.utils
from backend.tinvest_api import TOKEN


def mocked_now():
    dt = datetime.datetime(2020, 7, 24, 16, 45, 10)
    return dt


def test_current_price(mocker):
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())

    ticker = "VTBR"
    client = tinvest.SyncClient(TOKEN, use_sandbox=True)
    price = api.get_latest_price(ticker, client)
    assert price == 0.037875


def test_historical_price(mocker):
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())

    ticker = "VTBR"
    client = tinvest.SyncClient(TOKEN, use_sandbox=True)
    candles = api.get_candles_by_ticker(
        ticker,
        from_=backend.utils.custom_now.now() - datetime.timedelta(minutes=48),
        to=backend.utils.custom_now.now(),
        interval="1min",
        client=client,
    )
    candles = api.unpack_candles(candles)
    assert len(candles) == 42
