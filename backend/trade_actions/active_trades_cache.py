import pickle

from loguru import logger

from backend.utils import params


class Cache:
    @staticmethod
    def read():
        with open(params.pickle_cache, "rb") as f:
            cache = pickle.load(f)
        return cache

    @staticmethod
    def overwrite(thing):
        if not isinstance(thing, list):
            raise ValueError("Can only cache list")
        with open(params.pickle_cache, "wb") as f:
            pickle.dump(thing, f)

    @staticmethod
    def append(trade):
        trades: list = Cache.read()
        trades.append(trade)
        Cache.overwrite(thing=trades)

    @staticmethod
    def remove(trade):

        trades: list = Cache.read()
        trades_copy = trades.copy()
        deleted = False
        for trd in trades_copy:
            cond1 = trd.ticker_relation == trade.ticker_relation
            cond2 = trd.sentiment == trade.sentiment
            cond3 = trd.news_time == trade.news_time
            if cond1 and cond2 and cond3:
                trades.remove(trd)
                deleted = True
                continue
        if not deleted:
            logger.debug("Trade is not cached, can't delete.")
        Cache.overwrite(thing=trades)
