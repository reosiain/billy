import os
import pickle
import re

import pandas as pd

from backend.utils import params

if __name__ == "__main__":
    ticker_dict = {
        "LNTA": [re.compile(r"Лент")],
        "MAIL": [re.compile(r"(?i)Mail.ru"), re.compile(r"Мейл.ру")],
        "FIVE": [
            re.compile(r"X5"),
            re.compile(r"Пятерочк"),
            re.compile(r"Перекрест"),
            re.compile(r"X5 Retail"),
        ],
        "SBER": [re.compile(r"Сбер"), re.compile(r"Сбербанк")],
        "ROSN": [re.compile(r"Роснефт"), re.compile(r"Rosneft")],
        "GAZP": [re.compile(r"Газпром"), re.compile(r"Gazprom")],
        "NVTK": [re.compile(r"Новатек"), re.compile(r"Novatek")],
        "GMKN": [re.compile(r"Норникел"), re.compile(r"Nornikel")],
        "LKOH": [re.compile(r"Лукойл"), re.compile(r"Lukoil")],
        "PLZL": [
            re.compile(r"(?i)Плюс Золото"),
            re.compile(r"Полюс"),
            re.compile(r"Polyus"),
        ],
        "SIBN": [
            re.compile(r"Газпромнефт"),
            re.compile(r"Газпром нефт"),
            re.compile(r"Gazpromneft"),
            re.compile(r"(?i)Gazprom Neft"),
        ],
        "YNDX": [re.compile(r"Яндекс"), re.compile(r"Yandex")],
        "NLMK": [re.compile(r"НЛМК"), re.compile(r"NLMK")],
        "SNGS": [re.compile(r"Сургутнефтегаз"), re.compile(r"Surgutneftegas")],
        "TATN": [re.compile(r"Tatneft"), re.compile(r"Татнефть")],
        "CHMF": [re.compile(r"Severstal"), re.compile(r"Северстал")],
        "ALRS": [re.compile(r"Алроса"), re.compile(r"(?i)Alrosa")],
        "RUAL": [re.compile(r"Rusal"), re.compile(r"Русал")],
        "VTBR": [re.compile(r"VTB"), re.compile(r"ВТБ")],
        "POLY": [re.compile(r"Полиметал"), re.compile(r"Polymetal")],
        "MGNT": [re.compile(r"Магнит"), re.compile(r"Magnit")],
        "MAGN": [re.compile(r"ММК"), re.compile(r"MMK")],
        "MTSS": [re.compile(r"MTS"), re.compile(r"МТС")],
        "PIKK": [re.compile(r"ПИК"), re.compile(r"PIK")],
        "PHOR": [re.compile(r"Phosagro"), re.compile(r"Фосагро")],
        "BANE": [re.compile(r"Bashneft"), re.compile(r"Башнефт")],
        "HYDR": [re.compile(r"Русгидро")],
        "AFLT": [re.compile(r"Аэрофлот"), re.compile(r"Aeroflot")],
        "AFKS": [re.compile(r"АФК Система"), re.compile(r"AFK Sistema")],
        "TCSG": [
            re.compile(r"Тинькофф"),
            re.compile(r"Тиньков"),
            re.compile(r"TCS Group"),
            re.compile(r"TCS"),
        ],
        "OZON": [re.compile(r"Озон"), re.compile(r"Ozon")],
    }

    all_trades = os.listdir(params.trades_dump)
    table = pd.DataFrame(
        columns=[
            "news_time",
            "trade_time",
            "sentiment",
            "open_price",
            "close_price",
            "stop_loss",
            "ticker",
            "text",
            "companies",
        ]
    )

    for trade in all_trades:

        list_ = []
        f = open(params.trades_dump / trade, "rb")
        try:
            tr = pickle.load(f)
            f.close()

            list_.append(tr.news_time.strftime("%d.%m.%Y %H:%M:%S"))
            list_.append(tr.trade_time.strftime("%d.%m.%Y %H:%M:%S"))
            list_.append(tr.sentiment)
            list_.append(tr.open_price_apx)
            list_.append(tr.close_price_apx)
            list_.append(tr.stop_loss_trigger)
            list_.append(tr.ticker_relation)
            list_.append(tr.raw_text)
        except AttributeError:
            continue

        ticker_dict_tofill = {
            "LNTA": 0,
            "MAIL": 0,
            "FIVE": 0,
            "SBER": 0,
            "ROSN": 0,
            "GAZP": 0,
            "NVTK": 0,
            "GMKN": 0,
            "LKOH": 0,
            "PLZL": 0,
            "SIBN": 0,
            "YNDX": 0,
            "NLMK": 0,
            "SNGS": 0,
            "TATN": 0,
            "CHMF": 0,
            "ALRS": 0,
            "RUAL": 0,
            "VTBR": 0,
            "POLY": 0,
            "MGNT": 0,
            "MAGN": 0,
            "MTSS": 0,
            "PIKK": 0,
            "PHOR": 0,
            "BANE": 0,
            "HYDR": 0,
            "AFLT": 0,
            "AFKS": 0,
            "TCSG": 0,
            "OZON": 0,
        }

        for key in ticker_dict.keys():
            list_of_patterns = ticker_dict[key]
            single_key = [0]
            for pat in list_of_patterns:
                a = len(re.findall(pat, tr.raw_text))
                single_key.append(a)
            ticker_dict_tofill[key] = max(single_key)

        list_.append(ticker_dict_tofill)
        list_ = pd.DataFrame(
            list_,
            index=[
                "news_time",
                "trade_time",
                "sentiment",
                "open_price",
                "close_price",
                "stop_loss",
                "ticker",
                "text",
                "companies",
            ],
        )

        table = table.append(list_.T)

    table.to_csv(
        params.source_root / "source/report.csv", encoding="utf-8-sig", sep="@"
    )
