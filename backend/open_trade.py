import datetime
import threading
import time

import backend.dbio as db
import backend.flow_control as fc
import backend.telegram_bot.bot_poster as tbot
import telebot
from backend.stats import trade_stats
from backend.tinvest_api.functions import NoPriceError
from backend.trade_actions.active_trades_cache import Cache
from backend.trade_actions.trade_entity_class import (
    Trade,
    NoTargetError,
    MultiTargetError,
    ShallowSentimentError,
    ContextError,
)
from backend.utils import request_news
from loguru import logger


def close_all_trades() -> None:
    obj_list = Cache.read()
    for trade in obj_list:
        try:
            trade.close_trade_mock()
            ret = ((trade.close_price_apx / trade.open_price_apx) - 1) * 100
            if int(trade.sentiment) == 2:
                sent_type = "Long"
                multiple = 1
            elif int(trade.sentiment) == 0:
                sent_type = "Short"
                multiple = -1

            tbot.select_message_and_post(
                ticker=trade.ticker_relation,
                message_type=tbot.Messages.CLOSE,
                direction=sent_type,
                rtr=round(ret * multiple, 3),
                stop_loss=trade.stop_loss_trigger,
                cum_ret=trade_stats.get_daily_cum_return(),
            )
            Cache.remove(trade)

        except Exception:
            logger.exception(
                f"Error trying to close {trade.ticker_relation} ({trade.sentiment}). Removed"
            )
            Cache.remove(trade)
            continue


def check_closing_decision() -> None:
    obj_list = Cache.read()
    for trade in obj_list:

        try:
            des = trade.ready_to_close
        except NoPriceError:
            logger.error(
                f"Could not get price. Skipping check for {trade.ticker_relation} ({trade.sentiment})."
            )
            continue
        try:
            if des or trade.stop_loss_check:
                trade.close_trade_mock()

                ret = ((trade.close_price_apx / trade.open_price_apx) - 1) * 100
                if int(trade.sentiment) == 2:
                    sent_type = "Long"
                    multiple = 1
                elif int(trade.sentiment) == 0:
                    sent_type = "Short"
                    multiple = -1

                tbot.select_message_and_post(
                    ticker=trade.ticker_relation,
                    message_type=tbot.Messages.CLOSE,
                    direction=sent_type,
                    rtr=round(ret * multiple, 3),
                    stop_loss=trade.stop_loss_trigger,
                    cum_ret=trade_stats.get_daily_cum_return(),
                )
                Cache.remove(trade)

        except Exception:
            logger.exception(
                f"check_closing_decision method failed. Trade {trade.ticker_relation} ({trade.sentiment}) removed"
            )
            Cache.remove(trade)
            continue


def cycle(first=False) -> None:
    """Performs one full cycle of news checking and trade execution"""
    new_news = request_news.check_news(first)
    if len(new_news) == 0:
        check_closing_decision()
        return

    for news in new_news:
        db.db_client.store_news(news)

    # Get rid of news with wrong date format and then sort by time
    ch_new_news = new_news.copy()
    for news in ch_new_news:
        if not isinstance(news["time"], datetime.datetime):
            new_news.remove(news)
    new_news = sorted(new_news, key=lambda x: x["time"])

    for event in new_news:

        actual_comps = set(event["tickers"])

        try:
            if len(actual_comps) > 1:
                raise MultiTargetError
            if len(actual_comps) < 1:
                raise NoTargetError

        except NoTargetError:
            logger.error(f"Could not identify ticker")
            continue
        except MultiTargetError:
            logger.error(f'Multi-ticker in the news {" ".join(event["tickers"])}')
            continue

        time_ = event["time"]
        text = event["text"]
        ticker = event["tickers"][0]

        if ticker == "MOEX":
            logger.error(f"Not trading MOEX equity. Skipping")
            continue

        try:
            trade = Trade(time=time_, seq=text, ticker=ticker)
        except ShallowSentimentError:
            logger.error(f"Neutral sentiment for {ticker}")
            continue
        except NoPriceError:
            logger.error(f"Could not fetch price for {ticker}")
            continue
        except ContextError:
            logger.error(f"Found similar context for {ticker}")
            continue
        except Exception:
            logger.exception(
                f"trade class constructor failed. Skipping event for {ticker}"
            )
            continue

        try:
            if int(trade.sentiment) == 2:
                sent = "Long"
            elif int(trade.sentiment) == 0:
                sent = "Short"

            ok = fc.should_open(trade)
            if not ok:
                continue

            tbot.select_message_and_post(
                ticker=trade.ticker_relation,
                message_type=tbot.Messages.OPEN,
                direction=sent,
                price=trade.open_price_apx,
            )
            Cache.append(trade)

        except fc.AlreadyOpenError:
            logger.error(f"{ticker} with same direction is already open")
            continue

    check_closing_decision()


def main(
    p2k: threading.Event = None, bot: telebot.TeleBot = None, personal_token: str = None
) -> None:
    logger.add("source/log.txt",
        format="<green>{time:DD.MM.YY HH:mm:ss}</green> | <level>{level: <8}</level>|<cyan>{function}</cyan> - <level>{message}</level>",
    )
    logger.info("Starting..")
    first_run = True
    if p2k is None:
        while True:
            try:
                logger.debug("New cycle")
                cycle(first=first_run)
                first_run = False
                time.sleep(20)
            except Exception as error:
                logger.exception(f"Unexpected error. {error}")
                continue
    else:
        while not p2k.is_set():
            try:
                logger.debug("New cycle")
                cycle(first=first_run)
                first_run = False
                time.sleep(20)
            except Exception as error:
                logger.exception(f"Unexpected error. {error}")
                continue
        logger.debug("Stopped by p2k")


if __name__ == "__main__":
    main()
