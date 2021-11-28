import datetime

from backend import utils
from backend.dbio import db_client as db


def get_daily_cum_return(period=0) -> float:
    """Returns cum return for period days ago. Zero period for todays return"""

    start_date = utils.custom_now.now() - datetime.timedelta(days=period)
    start_date = datetime.datetime(start_date.year, start_date.month, start_date.day)

    filter_ = {"CLOSE_TIME_low": start_date}
    raw_trades = db.get_closed_trades(k=filter_)

    trades = []
    for trade in raw_trades:
        if trade["CLOSE_TIME"] is not None:
            trades.append(trade)

    trades = sorted(trades, key=lambda x: x["CLOSE_TIME"])

    retrs = []
    for trd in trades:
        retrs.append(trd["CALCULATED_RETURN"])

    cum = 1
    for ret in retrs:
        cum *= 1 + ret
    cum = cum * 100
    cum = round(cum, 2)
    return round(cum - 100, 2)


if __name__ == "__main__":
    a = get_daily_cum_return()
    print(a)
