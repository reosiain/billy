import datetime
import sys
from pathlib import Path

import backend.flow_control as fc
from backend.open_trade import cycle
from backend.trade_actions import active_trades_cache
from backend.trade_actions import trade_entity_class
from backend.trade_actions.active_trades_cache import Cache

sys.path.append(Path(__file__).parent.parent.__str__())
print(sys.path)

prepared_news = [
    {
        "hash": 8763240662373510832,
        "link": "https://www.finam.ru/analysis/newsitem/v-gazprome-poyasnili-kak-budet-osushestvlyatsya-tranzit-gaza-cherez-ukrainu-posle-2024-goda-20210724-223911/?utm_source=rss&utm_medium=new_compaigns&news_to_finamb=new_compaigns",
        "source": "finam01",
        "text": 'Глава "Газпрома" Алексей Миллер, допуская увеличение транзита через '
        "Украину, говорил о транспортировке после 2024 года в соответствии с "
        "новыми объемами закупок российского газа партнерами из стран ЕС, в "
        "первую очередь – из Германии, по новым контрактам, заявили в "
        'пресс-службе компании.|@|"Ознакомились с заявлением председателя '
        'правления "Нафтогаза Украины" Юрия Витренко. Обращаем внимание, что '
        "никто не предлагал Украине покупать российский газ. Речь идет об "
        "объемах транзита через Украину после 2024 года в соответствии с "
        "новыми объемами закупок российского газа компаниями стран ЕС по "
        "новым контрактам. И о том, что нас в этой связи, в том числе "
        'заботит вопрос декарбонизации экономики Европейского союза", - '
        'сказано в сообщении Управления информации "Газпрома".|@|',
        "tickers": ["GAZP"],
        "time": datetime.datetime(2021, 7, 24, 16, 45, 5),
        "title": 'В "Газпроме" пояснили, как будет осуществляться транзит газа через '
        "Украину после 2024 года",
    },
    {
        "hash": -2961836942536140372,
        "link": "https://1prime.ru/energy/20210724/834290562.html",
        "source": "prime04",
        "text": "МОСКВА, 24 июл — ПРАЙМ. Во вторник Сбербанк отчитался об итогах за 2 квартал 2021, показывая прекрасный "
        "результат.|@| Рентабельность собственного капитала выросла на 10%, достигнув исторически "
        "максимальных значений. При этом резервы по просрочкам продожают снижаться, показывая положительный тренд.",
        "tickers": ["SBER"],
        "time": datetime.datetime(2021, 7, 24, 16, 44),
        "title": "Хороший отчет Сбера",
    },
    {
        "hash": -4767566895698452423,
        "link": "https://1prime.ru/gas/20210724/834287774.html",
        "source": "prime04",
        "text": "МОСКВА, 24 июл — ПРАЙМ.  Цены на природный газ растут в США на фоне "
        "попыток противодействия администрации президента Джо Байдена "
        '"Северному потоку 2", свидетельствуют данные аналитиков.|@|Цены на '
        "газ, по данным экспертов из Ycharts, выросли более чем на 40% за "
        "год, а с январских 2,46 доллара за галлон (3,78 литра) достигли "
        "3,24 доллара, что составляет почти 32% роста за время работы "
        'Байдена.Аналитик рассказал, выгоден ли для "Газпрома" транзит через '
        "Украину|@|Отмечается, что цены на природный газ растут на фоне "
        'неудачных попыток администрации остановить строительство "Северного '
        'потока-2" и признания, что добиться этого не получится.|@|Цены на '
        "бензин за год прибавили примерно в этом же диапазоне. Согласно "
        "данным независимого бюро статистики и энергетической информации, в "
        "прошлом июне цена галлона в среднем составляла 2,17 доллара, в "
        "нынешнем — 3,16. Цены на топливо начали заметно расти с приходом "
        "администрации Байдена, последние полгода работы на посту бывшего "
        "президента Дональда Трампа галлон бензина стоил около 2,2 доллара. "
        "Больше 3 долларов за галлон американцы не платили с октября 2014 "
        "года.",
        "tickers": ["GAZP"],
        "time": datetime.datetime(2021, 7, 24, 16, 43, 30),
        "title": "Аналитики рассказали, почему цены на природный газ в США выросли "
        "на треть",
    },
]


def mocked_now():
    dt = datetime.datetime(2020, 7, 24, 16, 45, 10)
    return dt


def mock_msg():
    print("Message sent")


def test_one_cycle(mocker):
    print()

    init_cache = active_trades_cache.Cache.read()

    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())
    mocker.patch("rss_feed.check_feed.run", return_value=prepared_news)
    mocker.patch(
        "backend.telegram_bot.bot_poster.select_message_and_post", return_value=mock_msg
    )

    cycle()
    assert len(active_trades_cache.Cache.read()) > len(init_cache)

    active_trades_cache.Cache.overwrite(init_cache)


def test_check_same_direction(mocker):
    mocker.patch(
        "backend.telegram_bot.bot_poster.select_message_and_post", return_value=mock_msg
    )
    mocker.patch("backend.utils.custom_now.now", return_value=mocked_now())

    init_cache = Cache.read()
    trade1 = trade_entity_class.Trade(
        time=datetime.datetime(2020, 7, 24, 16, 49, 10),
        seq="Mock",
        ticker="GAZP",
        sentiment=2,
    )
    Cache.append(trade1)
    trade2 = trade_entity_class.Trade(
        time=datetime.datetime(2020, 7, 24, 16, 50, 10),
        seq="Mock",
        ticker="GAZP",
        sentiment=2,
    )
    try:
        ok = fc.should_open(trade2)
    except fc.AlreadyOpenError:
        assert True
        Cache.overwrite(init_cache)
        return
    assert False
