import datetime
import json
import pathlib
import typing

import backend.utils
import tinvest
from backend import tinvest_api as api
from backend.dbio import db_client as db
from backend.sentiment_models import sentence_similarity as ss
from backend.sentiment_models import transformer_model as sm
from backend.telegram_bot import bot_poster
from backend.trade_actions import exit_model as em
from backend.trade_actions.context_cloud import ContextCloud
from backend.utils import params
from loguru import logger


class StaleNewsException(Exception):
    pass


class ShallowSentimentError(Exception):
    """Predicted neutral sentiment"""

    pass


class NoTargetError(Exception):
    """No ticker for the news"""

    pass


class MultiTargetError(Exception):
    """Multiple companies mentioned in the article ticker for the news"""

    pass


class ContextError(Exception):
    """Trade with similar context is already open"""

    pass


class Trade:
    """Class which represents trades, info about trades and actions that can be done with trade"""

    def __init__(
        self,
        time: typing.Union[str, datetime.datetime],
        seq: str,
        ticker: str,
        sentiment: int = None,
    ):
        self.news_time = time
        self.raw_text = seq
        self.ticker_relation = ticker
        if sentiment is None:
            self.sentiment = sm.predict(seq)
        else:
            self.sentiment = sentiment

        if self.sentiment == 1:
            raise ShallowSentimentError("Can't infer direction of trade")

        new_context = self.check_context()
        if not new_context:
            raise ContextError("Similar context found in the context cloud")

        self.trade_time = self._get_now()
        self.open_price_apx = self._get_current_price()

        self.need_to_close = False
        self.stop_loss_trigger = False
        self.reverse_closed = False

        self.close_price_apx = None
        self.close_time = None

    def __repr__(self):
        dir_ = "LONG" if self.sentiment == 2 else "SHORT"
        dt = self.trade_time.strftime("%Y.%m.%d %H:%M:%S")
        return f"<{dir_} {self.ticker_relation} at {self.open_price_apx} ({dt})>"

    @property
    def is_long(self):
        if self.sentiment == 2:
            return True
        else:
            return False

    @staticmethod
    def _get_now():
        return backend.utils.custom_now.now()

    def _get_current_price(self, ago: int = 5) -> float:
        """Connects to Tinkoff API and gets latest closing price"""

        client = tinvest.SyncClient(api.TOKEN, use_sandbox=True)
        price = api.functions.get_latest_price(self.ticker_relation, client, diff=ago)
        return price

    def open_trade(self):
        pass

    def close_trade(self):
        pass

    def close_trade_mock(self):
        """Gets current price and backs_up information about trade"""
        try:
            self.close_price_apx = self._get_current_price()
        except api.functions.NoPriceError:
            if self.is_long:
                self.close_price_apx = self.open_price_apx - (
                    self.open_price_apx * 0.01
                )
            else:
                self.close_price_apx = self.open_price_apx + (
                    self.open_price_apx * 0.01
                )

            raise api.functions.NoPriceError(
                "No price found within 5 minute range. Closing with -1%"
            )

        self.close_time = self._get_now()
        self._dump_trade()

    def _dump_trade(self, directory=None) -> None:
        """Dumps trade object to json file"""

        to_dumper = trade_to_dict(self)
        if directory is None:
            directory = params.trades_dump
        f_name = f"{self.ticker_relation}_{self.close_time.strftime('%d%m%Y_%H%M%S')}_{self.sentiment}.json"
        json.dump(to_dumper, open(f"{directory}/{f_name}", "w"))
        db.store_closed_trade(to_dumper)
        bot_poster.send_trade(pathlib.Path(f"{directory}/{f_name}"))

    @property
    def ready_to_close(self):
        """Checks if a trade is ready to close.
        If trade is younger than 4 minutes - do not close.
        If trade is older than 4 hours - fource close.
        If current return is negative - do not close.
        Else predict exit with the model"""
        if (self._get_now() - self.trade_time).seconds <= 240:  # 4 minutes
            return False

        if (self._get_now() - self.news_time).seconds >= 14400:  # 4 hours
            self.need_to_close = True
            return True

        if self.need_to_close:
            return True

        current_price = self._get_current_price()
        current_return = current_price / self.open_price_apx

        # Forcefully keeping alive if negative return
        if self.is_long:
            if current_return < 1:
                return False
        else:
            if current_return > 1:
                return False

        try:
            decision = em.ready_to_close(
                self.ticker_relation,
                int(self.sentiment),
            )
        except ValueError:
            logger.error("Value Error in closing decision. Keeping alive.")
            return False

        if decision:
            self.need_to_close = True
            return True

    @property
    def stop_loss_check(self):
        """If return is less that -1% - close with stop loss"""

        check_price = self._get_current_price()
        diff = check_price / self.open_price_apx

        if self.is_long:
            if diff <= params.stop_loss[0]:  # 1% hardcoded
                self.stop_loss_trigger = True
                return True
            else:
                return False
        else:
            if diff >= params.stop_loss[1]:
                self.stop_loss_trigger = True
                return True
            else:
                return False

    def check_context(self):
        """True is new"""
        ticker = self.ticker_relation
        time = self.news_time
        sentiment = self.sentiment
        try:
            emb = ss.sentiment_weighted_text_embedding(self.raw_text)

            cld = ContextCloud()
            result = cld.not_in_context(
                ticker=ticker, time=time, sentiment=sentiment, embedding=emb
            )
            return result

        except Exception:
            logger.exception("Context checker failed")
            return True


def trade_to_dict(trd: Trade) -> dict:
    trd_dict = {}

    try:
        trd_dict["NEWS_TIME"] = trd.news_time.isoformat()
    except AttributeError:
        trd_dict["NEWS_TIME"] = trd.news_time

    trd_dict["CLOSE_TIME"] = trd.close_time.isoformat()
    try:
        trd_dict["UPTIME"] = (trd.close_time - trd.news_time).seconds
    except TypeError:
        trd_dict["UPTIME"] = None
    trd_dict["TICKER"] = trd.ticker_relation
    trd_dict["OPEN_PRICE"] = trd.open_price_apx
    trd_dict["CLOSE_PRICE"] = trd.close_price_apx
    trd_dict["SENTIMENT"] = "POSITIVE" if trd.sentiment == 2 else "NEGATIVE"
    modulo = 1 if trd.is_long else -1
    trd_dict["ABSOLUTE_RETURN"] = round(trd.close_price_apx / trd.open_price_apx, 5)
    trd_dict["CALCULATED_RETURN"] = round(
        ((trd.close_price_apx / trd.open_price_apx) - 1) * modulo, 5
    )
    trd_dict["SUCCESSFUL_TRADE"] = True if trd_dict["CALCULATED_RETURN"] > 0 else False
    trd_dict["IS_STOPLOSS"] = trd.stop_loss_trigger
    trd_dict["IS_REVERSED"] = trd.reverse_closed
    try:
        trd_dict["QUOTES"] = "&".join(trd.backup_quotes)
    except AttributeError:
        trd_dict["QUOTES"] = None
    trd_dict["TEXT"] = trd.raw_text

    return trd_dict
