import datetime
import os

from pymongo import MongoClient

client = MongoClient(os.getenv('MONGO_HOST'), 1002)
dumps = client["trades"]["trade_dumps"]
context = client["trades"]["context"]


def store_closed_trade(trade: dict):
    """Stores dict with closed trade in db"""
    global dumps

    if isinstance(trade["NEWS_TIME"], str) and isinstance(trade["CLOSE_TIME"], str):
        trade["NEWS_TIME"] = datetime.datetime.fromisoformat(trade["NEWS_TIME"])
        trade["CLOSE_TIME"] = datetime.datetime.fromisoformat(trade["CLOSE_TIME"])
    dumps.insert_one(trade)


def get_closed_trades(**k):
    """Filter db entries on a parameter dict. Additional params:
    CLOSE_TIME_low, CLOSE_TIME_high, NEWS_TIME_low, NEWS_TIME_high
    """

    global dumps
    filter_dict = {}

    for param in [
        "TICKER",
        "SENTIMENT",
        "SUCCESSFUL_TRADE",
        "IS_STOPLOSS",
        "IS_REVERSED",
    ]:
        if param in k.keys():
            filter_dict[param] = k[param]

    if "CLOSE_TIME_low" in k.keys() and "CLOSE_TIME_high" in k.keys():
        filter_dict["CLOSE_TIME"] = {
            "$lt": k["CLOSE_TIME_high"],
            "$gt": k["CLOSE_TIME_low"],
        }

    if "NEWS_TIME_low" in k.keys() and "NEWS_TIME_high" in k.keys():
        filter_dict["NEWS_TIME"] = {
            "$lt": k["NEWS_TIME_high"],
            "$gt": k["NEWS_TIME_low"],
        }

    if "CLOSE_TIME_low" in k.keys() and "CLOSE_TIME_high" not in k.keys():
        filter_dict["CLOSE_TIME"] = {"$gt": k["CLOSE_TIME_low"]}

    if "NEWS_TIME_low" in k.keys() and "NEWS_TIME_high" not in k.keys():
        filter_dict["NEWS_TIME"] = {"$gt": k["NEWS_TIME_low"]}

    res = dumps.find(filter_dict)

    output = []
    for elem in res:
        output.append(elem)
    return output


def _remove_closed_trade(trade: dict):
    """Removes dict with closed trade in db"""
    global dumps
    if isinstance(trade["NEWS_TIME"], str) and isinstance(trade["CLOSE_TIME"], str):
        trade["NEWS_TIME"] = datetime.datetime.fromisoformat(trade["NEWS_TIME"])
        trade["CLOSE_TIME"] = datetime.datetime.fromisoformat(trade["CLOSE_TIME"])
    dumps.delete_one(trade)


# ______________News storage

news_rss = client["news"]["from_feed"]
detailed_news = client["news"]["detailed_news"]


def read_cached_rss_links() -> set:
    """returns all processed links from db"""
    global news_rss
    res = news_rss.find({})
    output = set()
    for elem in res:
        output.add(elem["link"])
    return output


def store_rss_link(link):
    global news_rss
    data = {"link": link, "dt": datetime.datetime.now()}
    news_rss.insert_one(data)


def store_news(news: dict):
    global detailed_news
    detailed_news.insert_one(news)
