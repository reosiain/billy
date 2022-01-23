import json
import typing

import backend.telegram_bot.bot_poster as tbot
from backend.stats import trade_stats
from backend.trade_actions.active_trades_cache import Cache
from backend.trade_actions.trade_entity_class import Trade
from backend.trade_actions.trade_entity_class import trade_to_dict
from backend.utils import params


class AlreadyOpenError(Exception):
    pass


def should_open(trade: Trade) -> typing.Tuple[bool, float]:
    # Collect all active trades and directions
    active_trades: list = Cache.read()
    active_trades_and_directions = set()
    for trd in active_trades:
        tup = (trd.ticker_relation, trd.is_long)
        active_trades_and_directions.add(tup)

    # Check if trades are conflicting
    if (trade.ticker_relation, not trade.is_long) in active_trades_and_directions:
        for trd in active_trades:
            cond1 = trd.ticker_relation == trade.ticker_relation
            cond2 = trd.is_long == (not trade.is_long)
            if cond1 and cond2:
                trd.reverse_closed = True
                trd.close_trade_mock()
                break
        ret = ((trd.close_price_apx / trd.open_price_apx) - 1) * 100

        if int(trd.sentiment) == 2:
            sent = "Long"
            multiple = 1
        elif int(trd.sentiment) == 0:
            sent = "Short"
            multiple = -1
        else:
            raise ValueError("Wrong sentiment")

        tbot.select_message_and_post(
            ticker=trd.ticker_relation,
            message_type=tbot.Messages.REV_CLOSE,
            direction=sent,
            rtr=round(ret * multiple, 3),
            stop_loss=trd.stop_loss_trigger,
            cum_ret=trade_stats.get_daily_cum_return(),
        )

        _ = trade_to_dict(trade)
        f_name = f"{trade.ticker_relation}_{trade.close_time.strftime('%d%m%Y_%H%M%S')}_{trade.sentiment}.json"
        with open(params.trades_dump / f_name, "w") as file:
            json.dump(trade, file)
        Cache.remove(trd)
        return False

    elif (trade.ticker_relation, trade.is_long) in active_trades_and_directions:
        raise AlreadyOpenError(
            f"{trade.ticker_relation} with same direction is already open."
        )
    else:
        return True
