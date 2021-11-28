import datetime
import json
import os

import db_client

if __name__ == "__main__":

    base_path = "/home/stbarkhatov/billy_trades"
    files = os.listdir(base_path)

    for trd in files:

        if ".json" in trd:
            with open(base_path + "/" + trd, "rb") as f:
                _ = json.load(f)
            try:
                _["NEWS_TIME"] = datetime.datetime.fromisoformat(_["NEWS_TIME"])
            except:
                pass
            try:
                _["CLOSE_TIME"] = datetime.datetime.fromisoformat(_["CLOSE_TIME"])
            except:
                pass

            print(trd)
            db_client.store_closed_trade(_)
