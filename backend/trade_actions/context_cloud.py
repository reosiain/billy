import datetime

import backend.sentiment_models.sentence_similarity as ss
import numpy as np
from backend.dbio.db_client import client
from backend.utils import custom_now
from backend.utils import params

context = client["trades"]["context"]


class ContextCloud:
    """
    Context structure is ticker:dict - sentiment:list - (time, embedding):tuple

    ticker:
        sentiment1: [(time, emb), ]
        sentiment2: [(time, emb), ]

    """

    @staticmethod
    def store_context_vector(
        ticker: str, sentiment: int, embedding, time: datetime.datetime = None
    ):
        global context

        if time is not None:
            current_time = time
        else:
            current_time = custom_now.now()
        dump_ = {
            "ticker": ticker,
            "sentiment": sentiment,
            "time": current_time,
            "vector": embedding.tolist(),
        }
        context.insert_one(dump_)

    @staticmethod
    def _delete_entry(ticker: str, sentiment: int, time: datetime.datetime):
        global context
        context.delete_one({"ticker": ticker, "sentiment": sentiment, "time": time})

    @staticmethod
    def get_context_vectors(
        ticker: str, sentiment: int, time: datetime.datetime = None
    ):
        global context

        if time is None:
            now = custom_now.now()
            today = datetime.datetime(now.year, now.month, now.day)
        else:
            today = datetime.datetime(time.year, time.month, time.day)

        filter_dict = dict()
        filter_dict["ticker"] = ticker
        filter_dict["sentiment"] = sentiment
        filter_dict["time"] = {"$gt": today}

        res = context.find(filter_dict)
        output = []
        for elem in res:
            output.append(elem)
        return output

    @staticmethod
    def not_in_context(
        ticker: str, sentiment: int, embedding: np.array, time: datetime.datetime
    ):
        """Checks if same trade is already in the context"""

        contx = ContextCloud.get_context_vectors(
            ticker=ticker, sentiment=sentiment, time=time
        )
        if len(contx) == 0:
            return True

        scores = [0]
        for elem in contx:
            value = ss.compute_similarity(np.array(elem["vector"]), embedding)
            scores.append(value)
        if max(scores) >= params.similarity_threshold:
            return False

        ContextCloud.store_context_vector(
            ticker=ticker, sentiment=sentiment, embedding=embedding.tolist(), time=time
        )
        return True


if __name__ == "__main__":
    a = ContextCloud()
