import datetime
import pathlib

import backend.trade_actions.trade_entity_class
from backend.dbio import db_client
from backend.sentiment_models import sentence_similarity as ss
from backend.stats import trade_stats
from backend.trade_actions import exit_model as em
from backend.trade_actions import trade_entity_class
from backend.trade_actions.context_cloud import ContextCloud

text = """МОСКВА, 16 июл — ПРАЙМ. Сбербанк закрыл сделку по продаже акций материнской компании и долга "Евроцемента" 
    Михайловскому комбинату строительных материалов, сумма сделки составила 161 миллиард рублей, говорится в материалах 
    кредитной организации.|@|Банк в феврале сообщил, что приступает к публичному выбору покупателя ГК "Евроцемент". В к
    онтур сделки входят требования ПАО "Сбербанк" к ГК "Евроцемент" по кредитным и иным соглашениям, 100% акций GFI 
    Investments Limited (головной компании группы), 4% акций Eurocement Holding AG и требования, переданные 
    по договорам цессии от ООО "Сбербанк Инвестиции" к GFI. В апреле банк сообщил, что выбрал покупателя для актива, а
     сделка проходит согласование Федеральной антимонопольной службы.Экспорт газа "Газпрома" в дальнее зарубежье близок 
     к рекордному|@|"Сбербанк закрыл сделку по продаже акций материнской компании и долга Группы компаний "Евроцемент".
      Покупателем стала компания ООО "Михайловский комбинат строительных материалов" (ООО "МКСМ"), победившая в рамках 
      конкурентного запроса предложений, проведённого на электронной площадке Российского аукционного дома. Сумма
       сделки составила 161 млрд рублей", — сказано в документах.|@|Отмечается, что данная сделка окажет позитивное 
       влияние на финансовый результат группы Сбербанка."""


def mocked_now():
    dt = datetime.datetime(2020, 7, 24, 16, 45, 10)
    return dt


def test_trade_init(mocker):
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())

    date = datetime.datetime(2020, 7, 24, 16, 44, 15).strftime("%d-%m-%Y %H:%M:%S")
    ticker = "SBER"
    seq = text

    trd = trade_entity_class.Trade(seq=seq, ticker=ticker, time=date)
    assert trd.sentiment == 2


def test_close_decision(mocker):
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())

    ticker = "SBER"
    sentiment = 2
    dec = em.ready_to_close(ticker, sentiment)
    assert dec == False


def test_news_dump(mocker):
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())
    print()

    trade_count = db_client.get_closed_trades()
    date = datetime.datetime(2020, 7, 24, 16, 44, 15)
    ticker = "SBER"
    seq = text
    trd = trade_entity_class.Trade(seq=seq, ticker=ticker, time=date, sentiment=2)
    trd.close_time = datetime.datetime(2020, 7, 24, 17, 44, 15)
    trd.close_price_apx = 200
    trd._dump_trade()

    assert (len(db_client.get_closed_trades()) - len(trade_count)) == 1

    trade1 = trade_entity_class.trade_to_dict(trd)
    trade1["NEWS_TIME"] = datetime.datetime.fromisoformat(trade1["NEWS_TIME"])
    trade1["CLOSE_TIME"] = datetime.datetime.fromisoformat(trade1["CLOSE_TIME"])
    db_client._remove_closed_trade(trade1)


def test_cum(mocker):
    print()
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())

    dump_path = (pathlib.Path(__file__).parent / "trades").__str__()

    date = datetime.datetime(2020, 7, 24, 16, 44, 15)
    ticker = "SBER"
    seq = text
    trd = trade_entity_class.Trade(seq=seq, ticker=ticker, time=date, sentiment=2)
    trd.close_time = datetime.datetime(2020, 7, 24, 17, 44, 15)
    trd.close_price_apx = 200
    trd._dump_trade(directory=dump_path)
    trade1 = trade_entity_class.trade_to_dict(trd)

    date = datetime.datetime(2020, 7, 24, 10, 44, 15)
    ticker = "GAZP"
    trd = trade_entity_class.Trade(seq=seq, ticker=ticker, time=date, sentiment=2)
    trd.close_time = datetime.datetime(2020, 7, 24, 17, 45, 15)
    trd.close_price_apx = 190
    trd._dump_trade(directory=dump_path)
    trade2 = trade_entity_class.trade_to_dict(trd)

    a = trade_stats.get_daily_cum_return()
    trade1["NEWS_TIME"] = datetime.datetime.fromisoformat(trade1["NEWS_TIME"])
    trade1["CLOSE_TIME"] = datetime.datetime.fromisoformat(trade1["CLOSE_TIME"])
    trade2["NEWS_TIME"] = datetime.datetime.fromisoformat(trade2["NEWS_TIME"])
    trade2["CLOSE_TIME"] = datetime.datetime.fromisoformat(trade2["CLOSE_TIME"])

    db_client._remove_closed_trade(trade1)
    db_client._remove_closed_trade(trade2)

    assert a == -4.95


def test_context(mocker):
    print()
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())

    global text

    iconic_embedding = ss.sentiment_weighted_text_embedding(text)
    ticker, date, sentiment = "SBER", datetime.datetime(2020, 7, 24, 14, 44, 15), 2
    ContextCloud.store_context_vector(
        ticker=ticker, sentiment=sentiment, time=date, embedding=iconic_embedding
    )

    date2 = datetime.datetime(2020, 7, 24, 16, 44, 15)

    try:
        trade_entity_class.Trade(seq=text, ticker=ticker, time=date2, sentiment=2)

    except backend.trade_actions.trade_entity_class.ContextError:
        assert (
            len(ContextCloud.get_context_vectors(ticker=ticker, sentiment=sentiment))
            != 0
        )
        ContextCloud._delete_entry(ticker=ticker, sentiment=sentiment, time=date)
        ContextCloud._delete_entry(ticker=ticker, sentiment=sentiment, time=date2)
