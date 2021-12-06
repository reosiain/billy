import os
import threading

from fastapi import FastAPI
from pydantic import BaseModel
from backend.dbio import db_client

import backend.open_trade
from backend.stats import trade_stats

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

@app.get("/billy/stats/todays_return")
def todays_return():
    val = trade_stats.get_daily_cum_return()
    return {"stats": val}

@app.get("/billy/ping")
def list_source():
    return {'payload': os.listdir('source')}

#___ Mongo Reads

@app.get("/billy/db/show_open")
def show_open():
    open_files = list(db_client.cache.find())
    for file in open_files:
        file.pop('_id')
    return {'payload': open_files}

@app.get("/billy/db/latest_closed")
def show_open():
    open_files = trade_stats.fetch_latest_open_trades()
    for file in open_files:
        file.pop('_id')
    return {'payload': open_files}