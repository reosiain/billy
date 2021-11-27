import pathlib
from enum import Enum

import requests
import telegram
import yaml
from loguru import logger

from backend.utils import params

config = yaml.safe_load(open(params.tg_token, "rb"))
TOKEN = config["access_token"]
CHANNEL_ID = config["channel_id"]
TOKEN_TECHNICAL = config["access_token_van"]
PERSONAL_CHAT_ID = config["my_chat_id"]


class Messages(Enum):
    OPEN = "OPEN {ticker} - {direction} at {price}"
    CLOSE = "CLOSE: {ticker} - {direction}; \nReturn: {rtr}%; \nStop Loss {stop_loss}; \nCum return {cum_ret}%"
    REV_CLOSE = "CLOSE (reversed): {ticker} - {direction}; \nReturn: {rtr}%; \nStop Loss {stop_loss}; \nCum return: {cum_ret}%"


def select_message_and_post(ticker: str, message_type: Messages, **kwargs):
    direction = kwargs.get("direction")
    price = kwargs.get("price")
    rtr = kwargs.get("rtr")
    stop_loss = kwargs.get("stop_loss")
    cum_ret = kwargs.get("cum_ret")
    txt = message_type.value.format(
        ticker=ticker,
        direction=direction,
        price=price,
        rtr=rtr,
        stop_loss=stop_loss,
        cum_ret=cum_ret,
    )
    logger.info("\n" + txt)
    send_telegram(txt)


def send_telegram(text: str) -> None:
    url = "https://api.telegram.org/bot"
    url += TOKEN
    method = url + "/sendMessage"

    r = requests.post(method, data={"chat_id": CHANNEL_ID, "text": text})

    if r.status_code != 200:
        raise Exception("post_text error")


def send_trade(path: pathlib.Path) -> None:
    van_bot = telegram.Bot(token=TOKEN_TECHNICAL)
    with open(path, "rb") as file:
        van_bot.send_document(
            chat_id=int(PERSONAL_CHAT_ID),
            document=file,
            filename=path.parts[-1],
        )
    logger.info(f"Trade {path.parts[-1]} sent.")
