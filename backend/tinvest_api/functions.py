import datetime

import backend.utils
from tinvest.schemas import CandleResolution


class NoPriceError(Exception):
    pass


def get_figi_from_ticker(ticker: str, client) -> str:
    response = client.get_market_search_by_ticker(ticker)
    return response.payload.instruments[0].figi


def get_candles_by_ticker(ticker: str, from_: datetime, to: datetime, interval, client):
    figi_num = get_figi_from_ticker(ticker, client)
    response = client.get_market_candles(
        figi=figi_num, interval=CandleResolution(interval), from_=from_, to=to
    )
    if len(response.payload.candles) == 0:
        raise NoPriceError
    return response


def get_latest_price(ticker: str, client, diff: int = 5):
    figi_num = get_figi_from_ticker(ticker, client)
    response = client.get_market_candles(
        figi=figi_num,
        interval=CandleResolution("1min"),
        from_=backend.utils.custom_now.now() - datetime.timedelta(minutes=diff),
        to=backend.utils.custom_now.now(),
    )
    if len(response.payload.candles) == 0:
        raise NoPriceError
    candles = response.payload.candles
    latest = float(candles[-1].c)
    return latest


def unpack_candles(response) -> list:
    all_candles = response.payload.candles
    better_list = list()
    for candle in all_candles:
        this_candle = list()
        this_candle.append(candle.time)
        this_candle.append(float(candle.o))
        this_candle.append(float(candle.c))
        this_candle.append(float(candle.h))
        this_candle.append(float(candle.l))
        this_candle.append(float(candle.v))
        better_list.append(this_candle)

    return better_list
