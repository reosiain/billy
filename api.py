import os

from fastapi import FastAPI
from pydantic import BaseModel
import threading
import backend.open_trade

app = FastAPI()


class Item(BaseModel):
    first: bool


@app.get("/billy/run")
def run():

    global p2k
    global running_thread

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

    if not running_thread.is_alive():
        return {"message": "not running"}

    p2k.set()
    running_thread.join()

    return {"message": "stopped"}

@app.get("/billy/status")
def status():

    global running_thread

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

@app.get("/billy/ping")
def list_source():
    return {'payload':os.listdir('source')}


