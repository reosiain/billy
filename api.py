import os
import threading

from fastapi import FastAPI
from pydantic import BaseModel

import backend.open_trade
from backend.trade_actions.active_trades_cache import Cache
from backend.stats import trade_stats
import backend.telegram_bot as tg

app = FastAPI()


class Item(BaseModel):
    first: bool


global p2k
global running_thread

p2k = None
running_thread = None

@app.get("/billy/run")
def run():

    global p2k
    global running_thread

    if running_thread is not None:
        if running_thread.is_alive():
            return {"message": "already running"}

    p2k = threading.Event()
    running_thread = threading.Thread(
        target=backend.open_trade.main,
        kwargs={
            "p2k": p2k
        },
    )
    running_thread.start()

    return {"message": "started"}

@app.get("/billy/stop")
def shut():

    global p2k
    global running_thread

    if running_thread is not None:
        if not running_thread.is_alive():
            return {"message": "not running"}
    else:
        return {"message": "not running"}

    p2k.set()
    running_thread.join()

    return {"message": "stopped"}

@app.get("/billy/status")
def status():

    global running_thread

    if running_thread is not None:
        if running_thread.is_alive():
            return {"message": "running"}
    else:
        return {"message": "not running"}


@app.get("/billy/close_all")
def shut():

    try:
        backend.open_trade.close_all_trades()
        return {"message": 'closed'}
    except Exception:
        return {"message": 'error'}

@app.get("/billy/cache/read_names")
def read_cache():
    list_ = []
    actives = Cache.read()
    if len(actives) == 0:
        return {"cache": []}
    for item in actives:
        list_.append(item.__str__())
    return {"cache": list_}

@app.get("/billy/stats/todays_return")
def todays_return():
    val = trade_stats.get_daily_cum_return()
    return {"stats": val}

@app.get("/billy/ping")
def list_source():
    return {'payload':os.listdir('source')}


