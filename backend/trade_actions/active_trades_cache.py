from backend.dbio.db_client import cache
import backend.trade_actions.trade_entity_class as td


class Cache:
    @staticmethod
    def read():
        trades = list(cache.find())
        return [td.Trade(restored=True, restored_params =params) for params in trades]

    @staticmethod
    def append(trade):
        dicted_trade = td.trade_to_dict(trade)
        cache.insert_one(dicted_trade)

    @staticmethod
    def remove(trade):
        cache.delete_one({'TEXT':trade.raw_text})

    @staticmethod
    def count():
        return cache.count()

